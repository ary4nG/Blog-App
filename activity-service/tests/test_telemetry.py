"""
Unit tests for the telemetry module and AsyncElasticsearchTraceProcessor.

These tests validate the functionality of the telemetry configuration and the
asynchronous trace processor for Elasticsearch.
"""

import time
import threading
import json
from unittest.mock import Mock, patch
import pytest

import requests
from fastapi import FastAPI
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace import SpanContext
from app.telemetry.config import TelemetryManager, setup_telemetry
from app.telemetry.single_entry_trace_processor import AsyncElasticsearchTraceProcessor


class TestTelemetryManager:
    """Test cases for the TelemetryManager singleton class"""

    def test_singleton_pattern(self):
        """Test that TelemetryManager implements singleton pattern correctly"""
        instance1 = TelemetryManager()
        instance2 = TelemetryManager()

        assert instance1 is instance2

    # pylint: disable=protected-access
    @patch("app.telemetry.config.trace")
    @patch("app.telemetry.config.TracerProvider")
    @patch("opentelemetry.sdk.resources.Resource.create")
    @patch("app.telemetry.config.AsyncElasticsearchTraceProcessor")
    def test_initialize_once(
        self, mock_processor, mock_resource_create, mock_tracer_provider, mock_trace
    ):
        """Test that initialize is called only once even if called multiple times"""

        # Reset the singleton state before testing
        TelemetryManager._instance = None
        TelemetryManager._initialized = False

        mock_tracer_provider_instance = mock_tracer_provider.return_value
        mock_processor_instance = mock_processor.return_value

        manager = TelemetryManager()
        manager.initialize("test-app")
        manager.initialize("test-app-2")  # Should be ignored

        # Verify initialize was only executed once
        mock_resource_create.assert_called_once()
        mock_tracer_provider.assert_called_once()
        mock_trace.set_tracer_provider.assert_called_once_with(
            mock_tracer_provider_instance
        )
        mock_processor.assert_called_once()
        mock_tracer_provider_instance.add_span_processor.assert_called_once_with(
            mock_processor_instance
        )

    @patch("app.telemetry.config.FastAPIInstrumentor")
    @patch("app.telemetry.config.TelemetryManager")
    def test_setup_telemetry(self, mock_telemetry_manager, mock_instrumentation):
        """Test that setup_telemetry correctly initializes telemetry and instruments the app"""
        mock_manager_instance = mock_telemetry_manager.return_value

        test_app = FastAPI(title="test-app")

        setup_telemetry(test_app)

        # Verify the correct methods were called
        mock_telemetry_manager.assert_called_once()
        mock_manager_instance.initialize.assert_called_once_with("test-app")
        mock_instrumentation.instrument_app.assert_called_once_with(test_app)


# pylint: disable=protected-access
class TestAsyncElasticsearchTraceProcessor:
    """Test cases for the AsyncElasticsearchTraceProcessor class"""

    # Tests that need to access protected members
    @pytest.fixture
    def mock_readable_span(self):
        """Create a mock ReadableSpan for testing"""
        span = Mock(spec=ReadableSpan)
        context = Mock(spec=SpanContext)

        # Set required attributes
        context.trace_id = 0x12345678901234567890123456789012
        context.span_id = 0x1234567890123456
        span.get_span_context.return_value = context

        span.parent = None  # Make it a root span
        span.name = "test-span"
        span.attributes = {"http.status_code": 200, "request_method": "GET"}
        span.start_time = int(time.time() * 1e9)
        span.end_time = span.start_time + int(0.1 * 1e9)  # 100ms duration
        span.events = []

        return span

    @pytest.fixture
    def mock_child_span(self, mock_readable_span):
        """Create a mock child span for testing"""
        parent_context = mock_readable_span.get_span_context()

        child = Mock(spec=ReadableSpan)
        child_context = Mock(spec=SpanContext)

        child_context.trace_id = parent_context.trace_id
        child_context.span_id = 0x9876543210ABCDEF
        child.get_span_context.return_value = child_context

        child.parent = parent_context
        child.name = "child-span"
        child.attributes = {"db.statement": "SELECT 1"}
        child.start_time = mock_readable_span.start_time + int(0.01 * 1e9)
        child.end_time = child.start_time + int(0.05 * 1e9)  # 50ms duration
        child.events = []

        return child

    @pytest.fixture
    def processor(self):
        """Create a processor instance for testing"""
        # Use test configuration
        processor = AsyncElasticsearchTraceProcessor(
            elasticsearch_url="http://localhost:9200",
            index_prefix="test-app",
            queue_size=100,
            batch_size=10,
            export_timeout_secs=5,
        )
        yield processor

        # Ensure cleanup
        processor.shutdown()

    def test_initialization(self):
        """Test that the processor initializes correctly with given parameters"""
        processor = AsyncElasticsearchTraceProcessor(
            elasticsearch_url="http://test-es:9200",
            index_prefix="test-prefix",
            username="user",
            password="pass",
            queue_size=200,
            batch_size=20,
            export_timeout_secs=10,
        )

        assert processor.elasticsearch_url == "http://test-es:9200"
        assert processor.index_prefix == "test-prefix"
        assert processor.auth == ("user", "pass")
        assert processor.export_timeout == 10
        assert processor.batch_size == 20
        assert processor._export_queue.maxsize == 200
        assert isinstance(processor._worker_thread, threading.Thread)
        assert processor._worker_thread.is_alive()

        # Cleanup
        processor.shutdown()

    def test_on_start_is_noop(self, processor, mock_readable_span):
        """Test that on_start is a no-op method"""
        # on_start should do nothing, so this should not raise any exceptions
        processor.on_start(mock_readable_span)

    def test_on_end_buffers_spans(self, processor, mock_child_span):
        """Test that on_end adds spans to the trace buffer when they're not root spans"""
        trace_id = format(mock_child_span.get_span_context().trace_id, "032x")

        # Call on_end for a child span
        processor.on_end(mock_child_span)

        # Verify span was added to trace buffer
        assert trace_id in processor.trace_buffer
        assert len(processor.trace_buffer[trace_id]) == 1
        assert processor.trace_buffer[trace_id][0] is mock_child_span

    def test_on_end_processes_root_span(self, processor, mock_readable_span):
        """Test that on_end processes the entire trace when a root span is completed"""
        trace_id = format(mock_readable_span.get_span_context().trace_id, "032x")

        with patch.object(processor, "_export_queue") as mock_queue:
            # Call on_end for root span
            processor.on_end(mock_readable_span)

            # Verify span was processed and added to export queue
            assert (
                trace_id not in processor.trace_buffer
            )  # Should be removed from buffer
            mock_queue.put.assert_called_once()

            # Verify the structure of the exported data
            exported_entry = mock_queue.put.call_args[0][0]
            assert exported_entry["trace_id"] == trace_id
            assert "duration_ms" in exported_entry
            assert "start_time" in exported_entry
            assert "end_time" in exported_entry
            assert exported_entry["response_status_code"] == 200
            assert "message" in exported_entry

    def test_on_end_processes_full_trace(
        self, processor, mock_readable_span, mock_child_span
    ):
        """Test that on_end processes all spans in a trace when root span is completed"""
        trace_id = format(mock_readable_span.get_span_context().trace_id, "032x")

        with patch.object(processor, "_export_queue") as mock_queue:
            processor.on_end(mock_child_span)
            processor.on_end(mock_readable_span)

            assert trace_id not in processor.trace_buffer
            mock_queue.put.assert_called_once()

            # Check that both spans are in the message
            exported_entry = mock_queue.put.call_args[0][0]
            message = json.loads(exported_entry["message"])
            assert len(message) == 2

            # Verify spans have the expected structure
            span_names = [span["name"] for span in message]
            assert "test-span" in span_names
            assert "child-span" in span_names

    def test_collect_batch_from_queue(self, processor):
        """Test that _collect_batch_from_queue collects items from the queue correctly"""
        # Add test items to the queue
        for i in range(5):
            processor._export_queue.put(f"test-item-{i}")

        batch = processor._collect_batch_from_queue()

        # Verify batch contents
        assert len(batch) == 5
        assert all(f"test-item-{i}" in batch for i in range(5))
        assert processor._export_queue.empty()

    def test_collect_batch_empty_queue(self, processor):
        """Test that _collect_batch_from_queue handles empty queue correctly"""
        batch = processor._collect_batch_from_queue()
        assert batch == []

    @patch("requests.post")
    def test_send_batch_to_elasticsearch(self, mock_post, processor):
        """Test that _send_batch_to_elasticsearch sends data correctly"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        entries = [{"trace_id": f"test-{i}", "value": i} for i in range(3)]

        processor._send_batch_to_elasticsearch(entries)

        # Verify request was made correctly
        mock_post.assert_called_once()

        url = mock_post.call_args[0][0]
        assert "http://localhost:9200/_bulk" == url

        # Check data contains all entries
        data = mock_post.call_args[1]["data"]
        assert "test-0" in data
        assert "test-1" in data
        assert "test-2" in data

    @patch("requests.post")
    def test_send_batch_handles_errors(self, mock_post, processor):
        """Test that _send_batch_to_elasticsearch handles HTTP errors correctly"""
        # Setup mock to raise exception
        mock_post.side_effect = requests.RequestException("Test error")

        entries = [{"trace_id": "test"}]

        # This should not raise an exception
        processor._send_batch_to_elasticsearch(entries)

    @patch("time.sleep")
    def test_shutdown(self, processor):
        """Test that shutdown correctly signals the worker thread to stop"""
        # Add a test item to ensure queue isn't empty
        processor._export_queue.put("test-item")

        processor.shutdown()

        # Verify shutdown was signaled
        assert processor._shutdown.is_set()

        # Wait a moment for thread to process the shutdown signal
        time.sleep(0.1)

        # Verify queue was processed
        assert processor._export_queue.empty()
