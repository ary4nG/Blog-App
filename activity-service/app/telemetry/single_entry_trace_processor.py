"""OpenTelemetry span processor for exporting trace data to Elasticsearch asynchronously.

This module provides a custom span processor implementation that collects
OpenTelemetry traces and exports them directly to the Elasticsearch in a non-blocking manner.
It uses a background thread with a queue to prevent adding latency to API requests.
"""

import json
import logging
import threading
import queue
import time
from datetime import datetime, timezone
import requests
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanProcessor


class AsyncElasticsearchTraceProcessor(SpanProcessor):
    """A span processor that collects and forwards trace data to Elasticsearch asynchronously."""

    def __init__(
        self,
        elasticsearch_url,
        index_prefix,
        username=None,
        password=None,
        queue_size=10000,
        batch_size=100,
        export_timeout_secs=30,
    ):
        """Initialize the Elasticsearch trace processor with background worker

        Args:
            elasticsearch_url: The URL of the Elasticsearch instance
            index_prefix: Prefix for Elasticsearch index names
            username: Optional username for Elasticsearch authentication
            password: Optional password for Elasticsearch authentication
            queue_size: Maximum size of the export queue
            batch_size: Number of traces to export in a single batch
            export_timeout_secs: Timeout in seconds for Elasticsearch requests
        """
        self.elasticsearch_url = elasticsearch_url
        self.index_prefix = index_prefix
        self.auth = (username, password) if username and password else None
        self.export_timeout = export_timeout_secs
        self.batch_size = batch_size

        # Setup logging
        self.logger = logging.getLogger("async_trace_processor")
        self.logger.setLevel(logging.INFO)

        # Trace buffer stores spans by trace ID until root span completes
        self.trace_buffer = {}
        self._buffer_lock = threading.Lock()

        # Queue for sending to Elasticsearch asynchronously
        self._export_queue = queue.Queue(maxsize=queue_size)
        self._shutdown = threading.Event()

        # Start worker thread
        self._worker_thread = threading.Thread(
            target=self._worker, daemon=True, name="elasticsearch-trace-exporter"
        )
        self._worker_thread.start()

    def on_start(self, span, parent_context=None):
        """Called when a span starts.
        This implementation is a no-op as spans are processed only upon completion."""

    def on_end(self, span: ReadableSpan):
        """Called when a span ends, processing completed spans and
        queuing traces for export to Elasticsearch."""
        context = span.get_span_context()
        trace_id = format(context.trace_id, "032x")

        with self._buffer_lock:
            if trace_id not in self.trace_buffer:
                self.trace_buffer[trace_id] = []
            self.trace_buffer[trace_id].append(span)

            # If this is a root span (HTTP API call), process the entire trace
            if span.parent is None or span.parent.span_id == 0:
                trace_spans = self.trace_buffer.pop(trace_id, [])

                # Convert all spans to a serializable format
                spans_data = []
                for s in trace_spans:
                    s_context = s.get_span_context()
                    s_attributes = s.attributes or {}
                    parent_id = ""
                    if s.parent:
                        parent_id = format(s.parent.span_id, "016x")

                    spans_data.append(
                        {
                            "name": s.name,
                            "span_id": format(s_context.span_id, "016x"),
                            "parent_id": parent_id,
                            "start_time": s.start_time,
                            "end_time": s.end_time,
                            "duration_ms": (s.end_time - s.start_time) / 1000000,
                            "attributes": {k: str(v) for k, v in s_attributes.items()},
                            "exception_events": [
                                {
                                    "name": event.name,
                                    "timestamp": event.timestamp,
                                    "attributes": {
                                        k: str(v)
                                        for k, v in (event.attributes or {}).items()
                                    },
                                }
                                for event in s.events
                                if event.name == "exception"
                            ],
                        }
                    )

                # Get root span attributes
                attributes = span.attributes or {}

                # Create custom entry with required fields
                custom_entry = {
                    "trace_id": trace_id,
                    "correlation_id": attributes.get("correlation_id", ""),
                    "duration_ms": (span.end_time - span.start_time) / 1000000,
                    "start_time": datetime.fromtimestamp(
                        span.start_time / 1e9, tz=timezone.utc
                    ).isoformat(),
                    "end_time": datetime.fromtimestamp(
                        span.end_time / 1e9, tz=timezone.utc
                    ).isoformat(),
                    "response_status_code": attributes.get("http.status_code", 0),
                    "message": json.dumps(spans_data),
                    "request_method": attributes.get("request_method", ""),
                    "request_url": attributes.get("request_url", ""),
                    "app_name": attributes.get("app_name", ""),
                    "app_version": attributes.get("app_version", ""),
                    "environment": attributes.get("environment", ""),
                }

                # Add to export queue instead of sending directly
                try:
                    # Non-blocking put with a timeout to avoid getting stuck
                    self._export_queue.put(custom_entry, block=True, timeout=1)
                except queue.Full:
                    self.logger.warning(
                        "Trace export queue is full. Dropping trace: %s", trace_id
                    )

            # Clean up old traces occasionally
            if len(self.trace_buffer) > 1000:  # Arbitrary limit
                oldest_trace = next(iter(self.trace_buffer))
                del self.trace_buffer[oldest_trace]

    def _worker(self):
        """Background worker thread that processes the export queue."""
        self.logger.info("Elasticsearch trace export worker started")

        while not self._shutdown.is_set() or not self._export_queue.empty():
            batch = self._collect_batch_from_queue()
            if batch:
                self._send_batch_to_elasticsearch(batch)

        self.logger.info("Elasticsearch trace export worker shutting down")

    def _collect_batch_from_queue(self):
        """Collect a batch of items from the queue."""
        batch = []

        try:
            # Get at least one item (blocking)
            item = self._export_queue.get(block=True, timeout=0.5)
            batch.append(item)
            self._export_queue.task_done()

            # Try to get more items up to batch_size without blocking
            for _ in range(self.batch_size - 1):
                try:
                    item = self._export_queue.get(block=False)
                    batch.append(item)
                    self._export_queue.task_done()
                except queue.Empty:
                    break
        except queue.Empty:
            pass

        return batch

    def _send_batch_to_elasticsearch(self, entries):
        """Send a batch of telemetry entries to Elasticsearch using bulk API.

        Args:
            entries: List of trace entries to send to Elasticsearch
        """
        if not entries:
            return

        # Create date-based index name
        date_suffix = datetime.now().strftime("%Y.%m.%d")
        index_name = f"{self.index_prefix}-{date_suffix}"

        try:
            # Prepare bulk request body
            bulk_body = ""
            for entry in entries:
                # Add action line
                action = {"index": {"_index": index_name}}
                bulk_body += json.dumps(action) + "\n"

                # Add document line
                bulk_body += json.dumps(entry) + "\n"

            # Make the HTTP request to Elasticsearch bulk API
            url = f"{self.elasticsearch_url}/_bulk"
            headers = {"Content-Type": "application/x-ndjson"}

            response = requests.post(
                url,
                headers=headers,
                data=bulk_body,
                auth=self.auth,
                timeout=self.export_timeout,
            )

            if 200 <= response.status_code < 300:
                self.logger.info(
                    "Successfully sent %d traces to Elasticsearch bulk API with status code %d",
                    len(entries),
                    response.status_code,
                )
            else:
                self.logger.error(
                    "Failed to send traces to Elasticsearch: status=%s, response=%s",
                    response.status_code,
                    response.text[:200],  # Truncate long responses
                )
        except requests.RequestException as e:
            self.logger.error(
                "HTTP error sending telemetry to Elasticsearch: %s", str(e)
            )
        except json.JSONDecodeError as e:
            self.logger.error("JSON serialization error: %s", str(e))
        except (ValueError, TypeError) as e:
            self.logger.error("Data formatting error sending telemetry: %s", str(e))
        except Exception as e:
            self.logger.error(
                "Unexpected error sending telemetry to Elasticsearch: %s", str(e)
            )

    def shutdown(self):
        """Signal worker thread to finish processing and shut down."""
        self.logger.info("Shutting down Elasticsearch trace processor...")
        self._shutdown.set()

        # Wait for the queue to be fully processed
        try:
            # Manual timeout implementation
            end_time = time.time() + 5.0  # 5 seconds from now
            while time.time() < end_time:
                # Check if queue is empty
                if self._export_queue.empty():
                    break
                time.sleep(0.1)  # Short sleep to avoid CPU spinning
        except (ValueError, RuntimeError) as e:
            self.logger.warning(
                "Error while waiting for export queue to empty: %s", str(e)
            )
        except KeyboardInterrupt:
            self.logger.warning("Shutdown interrupted by user")

        # Wait for the worker thread to finish
        self._worker_thread.join(timeout=5.0)
        self.logger.info("Elasticsearch trace processor shutdown complete")
