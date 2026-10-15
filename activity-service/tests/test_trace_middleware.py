"Test suite for trace_middleware.py"


class TestTraceMiddleware:
    """Test cases for request tracing functionality"""

    def test_trace_headers_added(self, client):
        """Test that trace headers are added to response"""
        response = client.get(
            "/PROJECT_NAME_PLACEHOLDER/sample",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert "X-Correlation-ID" in response.headers

    def test_custom_trace_ids(self, client):
        """Test that custom trace IDs are preserved"""
        correlation_id = "test-correlation-id"

        response = client.get(
            "/PROJECT_NAME_PLACEHOLDER/sample",
            headers={
                "Authorization": "Bearer valid-token",
                "X-Correlation-ID": correlation_id,
            },
        )

        assert response.headers["X-Correlation-ID"] == correlation_id
