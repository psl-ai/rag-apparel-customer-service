from httpx import ASGITransport, AsyncClient


async def test_live_health_returns_response_envelope():
    from app.main import create_app

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health/live")

    body = response.json()
    assert response.status_code == 200
    assert body["code"] == "OK"
    assert body["message"] == "success"
    assert body["data"] == {"status": "ok"}
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
