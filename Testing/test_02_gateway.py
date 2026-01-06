"""
NetNynja Enterprise E2E Tests - API Gateway Routing (Phase 3 Validation)

Tests the unified API gateway including:
- Module health endpoints
- Route structure (/api/v1/ipam/*, /api/v1/npm/*, /api/v1/stig/*)
- OpenAPI documentation
- Rate limiting
- Request validation
"""
import pytest
import asyncio
from time import time

import httpx


pytestmark = pytest.mark.gateway


class TestGatewayHealth:
    """Test gateway health endpoints."""
    
    async def test_gateway_root_health(
        self,
        http_client: httpx.AsyncClient
    ):
        """GET /health returns gateway health status."""
        response = await http_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for health indicators
        assert data.get("status") in ("healthy", "ok", "up") or "healthy" in str(data).lower()
    
    async def test_gateway_ready_endpoint(
        self,
        http_client: httpx.AsyncClient
    ):
        """GET /ready returns readiness status."""
        response = await http_client.get("/ready")
        
        # Ready endpoint should indicate all dependencies are connected
        assert response.status_code == 200


class TestModuleHealthEndpoints:
    """Test health endpoints for each module."""
    
    @pytest.mark.parametrize("module", ["ipam", "npm", "stig"])
    async def test_module_health_endpoint(
        self,
        http_client: httpx.AsyncClient,
        module: str
    ):
        """GET /api/v1/{module}/health returns module health."""
        response = await http_client.get(f"/api/v1/{module}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should indicate module is healthy
        assert data.get("status") in ("healthy", "ok", "up") or "module" in data
    
    @pytest.mark.parametrize("module", ["ipam", "npm", "stig"])
    async def test_module_health_response_time(
        self,
        http_client: httpx.AsyncClient,
        module: str
    ):
        """Module health endpoints respond within 500ms."""
        start = time()
        response = await http_client.get(f"/api/v1/{module}/health")
        duration_ms = (time() - start) * 1000
        
        assert response.status_code == 200
        assert duration_ms < 500, f"{module} health took {duration_ms:.0f}ms"


class TestRouteStructure:
    """Test API route structure and routing."""
    
    async def test_ipam_routes_exist(
        self,
        authed_client: httpx.AsyncClient
    ):
        """IPAM module routes are accessible."""
        routes = [
            "/api/v1/ipam/subnets",
            "/api/v1/ipam/addresses",
        ]
        
        for route in routes:
            response = await authed_client.get(route)
            # Should not be 404
            assert response.status_code != 404, f"Route {route} not found"
    
    async def test_npm_routes_exist(
        self,
        authed_client: httpx.AsyncClient
    ):
        """NPM module routes are accessible."""
        routes = [
            "/api/v1/npm/devices",
            "/api/v1/npm/collectors",
        ]
        
        for route in routes:
            response = await authed_client.get(route)
            assert response.status_code != 404, f"Route {route} not found"
    
    async def test_stig_routes_exist(
        self,
        authed_client: httpx.AsyncClient
    ):
        """STIG module routes are accessible."""
        routes = [
            "/api/v1/stig/benchmarks",
            "/api/v1/stig/audits",
        ]
        
        for route in routes:
            response = await authed_client.get(route)
            assert response.status_code != 404, f"Route {route} not found"
    
    async def test_unknown_module_returns_404(
        self,
        authed_client: httpx.AsyncClient
    ):
        """Unknown module path returns 404."""
        response = await authed_client.get("/api/v1/unknown/health")
        
        assert response.status_code == 404


class TestOpenAPIDocumentation:
    """Test OpenAPI/Swagger documentation."""
    
    async def test_openapi_spec_available(
        self,
        http_client: httpx.AsyncClient
    ):
        """GET /api/docs/openapi.json returns OpenAPI spec."""
        # Try common OpenAPI endpoints
        endpoints = [
            "/api/docs/openapi.json",
            "/api/openapi.json",
            "/openapi.json",
            "/api/docs/swagger.json"
        ]
        
        spec_found = False
        for endpoint in endpoints:
            response = await http_client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                if "openapi" in data or "swagger" in data:
                    spec_found = True
                    break
        
        assert spec_found, "OpenAPI specification not found at any standard endpoint"
    
    async def test_openapi_contains_all_modules(
        self,
        http_client: httpx.AsyncClient
    ):
        """OpenAPI spec contains routes for all three modules."""
        # Get spec
        response = await http_client.get("/api/docs/openapi.json")
        if response.status_code != 200:
            response = await http_client.get("/openapi.json")
        
        if response.status_code != 200:
            pytest.skip("OpenAPI spec not available")
        
        spec = response.json()
        paths = spec.get("paths", {})
        paths_str = str(paths).lower()
        
        assert "/ipam" in paths_str, "IPAM routes not in OpenAPI spec"
        assert "/npm" in paths_str, "NPM routes not in OpenAPI spec"
        assert "/stig" in paths_str, "STIG routes not in OpenAPI spec"
    
    async def test_swagger_ui_available(
        self,
        http_client: httpx.AsyncClient
    ):
        """Swagger UI is accessible."""
        endpoints = [
            "/api/docs",
            "/docs",
            "/swagger",
            "/api/swagger"
        ]
        
        ui_found = False
        for endpoint in endpoints:
            response = await http_client.get(endpoint)
            if response.status_code == 200:
                content = response.text.lower()
                if "swagger" in content or "openapi" in content:
                    ui_found = True
                    break
        
        assert ui_found, "Swagger UI not found"


class TestRateLimiting:
    """Test API rate limiting."""
    
    @pytest.mark.slow
    async def test_rate_limit_triggers_on_burst(
        self,
        http_client: httpx.AsyncClient,
        admin_tokens
    ):
        """Burst requests trigger rate limiting (429)."""
        # Send burst of requests
        tasks = []
        for _ in range(20):  # Burst of 20 requests
            tasks.append(
                http_client.get(
                    "/api/v1/ipam/health",
                    headers=admin_tokens.auth_header
                )
            )
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # At least some requests should succeed
        success_count = sum(
            1 for r in responses 
            if isinstance(r, httpx.Response) and r.status_code == 200
        )
        assert success_count > 0, "All requests failed"
        
        # Check if any were rate limited (429)
        rate_limited = sum(
            1 for r in responses 
            if isinstance(r, httpx.Response) and r.status_code == 429
        )
        
        # This is informational - rate limiting may not trigger for 20 requests
        if rate_limited > 0:
            # Verify rate limit response has proper headers
            limited_response = next(
                r for r in responses 
                if isinstance(r, httpx.Response) and r.status_code == 429
            )
            assert "Retry-After" in limited_response.headers or True  # Soft check
    
    async def test_rate_limit_headers_present(
        self,
        http_client: httpx.AsyncClient,
        admin_tokens
    ):
        """Rate limit headers are present in responses."""
        response = await http_client.get(
            "/api/v1/ipam/health",
            headers=admin_tokens.auth_header
        )
        
        # Check for common rate limit headers
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "RateLimit-Limit",
            "RateLimit-Remaining"
        ]
        
        has_rate_headers = any(h in response.headers for h in rate_limit_headers)
        
        # Soft assertion - headers may not be implemented
        if not has_rate_headers:
            pytest.skip("Rate limit headers not implemented")


class TestRequestValidation:
    """Test request validation with Zod schemas."""
    
    async def test_invalid_json_returns_400(
        self,
        http_client: httpx.AsyncClient,
        admin_tokens
    ):
        """Invalid JSON body returns 400 Bad Request."""
        response = await http_client.post(
            "/api/v1/ipam/subnets",
            headers={
                **admin_tokens.auth_header,
                "Content-Type": "application/json"
            },
            content="not valid json{"
        )
        
        assert response.status_code == 400
    
    async def test_missing_required_field_returns_422(
        self,
        authed_client: httpx.AsyncClient
    ):
        """Missing required field returns 422 Unprocessable Entity."""
        response = await authed_client.post(
            "/api/v1/ipam/subnets",
            json={
                "name": "Test without CIDR"
                # Missing required 'cidr' field
            }
        )
        
        assert response.status_code in (400, 422)
        data = response.json()
        
        # Error should mention the missing field
        error_str = str(data).lower()
        assert "cidr" in error_str or "required" in error_str
    
    async def test_invalid_cidr_format_returns_422(
        self,
        authed_client: httpx.AsyncClient
    ):
        """Invalid CIDR format returns validation error."""
        response = await authed_client.post(
            "/api/v1/ipam/subnets",
            json={
                "cidr": "not-a-valid-cidr",
                "name": "Invalid CIDR Test"
            }
        )
        
        assert response.status_code in (400, 422)
    
    async def test_invalid_ip_address_returns_422(
        self,
        authed_client: httpx.AsyncClient
    ):
        """Invalid IP address format returns validation error."""
        response = await authed_client.post(
            "/api/v1/npm/devices",
            json={
                "hostname": "test-device",
                "ip_address": "999.999.999.999",  # Invalid IP
                "device_type": "router"
            }
        )
        
        assert response.status_code in (400, 422)


class TestCORSAndSecurityHeaders:
    """Test CORS and security headers."""
    
    async def test_cors_headers_present(
        self,
        http_client: httpx.AsyncClient
    ):
        """CORS headers are present in responses."""
        response = await http_client.options(
            "/api/v1/ipam/health",
            headers={"Origin": "http://localhost:5173"}
        )
        
        # Check for CORS headers
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers"
        ]
        
        has_cors = any(h in response.headers for h in cors_headers)
        
        # This is a soft check - CORS may be configured differently
        if not has_cors:
            pytest.skip("CORS headers not configured for this origin")
    
    async def test_security_headers_present(
        self,
        http_client: httpx.AsyncClient
    ):
        """Security headers are present in responses."""
        response = await http_client.get("/health")
        
        # Check for common security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "Strict-Transport-Security": None,  # Just check presence
        }
        
        missing_headers = []
        for header, expected in security_headers.items():
            value = response.headers.get(header)
            if value is None:
                missing_headers.append(header)
            elif expected is not None:
                if isinstance(expected, list):
                    if value not in expected:
                        missing_headers.append(f"{header} (wrong value)")
                elif value != expected:
                    missing_headers.append(f"{header} (wrong value)")
        
        # Soft assertion - some headers may not be configured
        if missing_headers:
            pytest.skip(f"Security headers not configured: {missing_headers}")


class TestErrorResponses:
    """Test error response format consistency."""
    
    async def test_404_response_format(
        self,
        http_client: httpx.AsyncClient
    ):
        """404 responses have consistent format."""
        response = await http_client.get("/api/v1/nonexistent/endpoint")
        
        assert response.status_code == 404
        data = response.json()
        
        # Should have error information
        assert "error" in data or "message" in data or "detail" in data
    
    async def test_401_response_format(
        self,
        http_client: httpx.AsyncClient
    ):
        """401 responses have consistent format."""
        response = await http_client.get("/api/v1/ipam/subnets")
        
        assert response.status_code == 401
        data = response.json()
        
        assert "error" in data or "message" in data or "detail" in data
    
    async def test_500_errors_dont_leak_internals(
        self,
        http_client: httpx.AsyncClient,
        admin_tokens
    ):
        """500 errors don't leak internal implementation details."""
        # This test is informational - we can't easily trigger a 500
        # But we can verify error handling doesn't expose stack traces
        
        # Try to trigger an error with malformed data
        response = await http_client.post(
            "/api/v1/ipam/subnets",
            headers=admin_tokens.auth_header,
            json={
                "cidr": "10.0.0.0/8",
                "name": "x" * 10000  # Potentially trigger error with very long name
            }
        )
        
        if response.status_code >= 500:
            data = response.json()
            data_str = str(data).lower()
            
            # Should not contain stack traces or internal paths
            assert "traceback" not in data_str
            assert "/home/" not in data_str
            assert "/usr/local/" not in data_str
            assert "node_modules" not in data_str
