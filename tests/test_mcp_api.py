from fastapi.testclient import TestClient

from app.mcp.api import app


client = TestClient(app)


def test_mcp_info_endpoint() -> None:
    response = client.get("/info")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["result"]["name"] == "stock-agent-mcp"


def test_mcp_tools_endpoint_exposes_tool_specs() -> None:
    response = client.get("/tools")
    assert response.status_code == 200
    payload = response.json()
    tools = payload["result"]["tools"]
    assert any(tool["name"] == "get_stock_price" for tool in tools)
    assert any("inputSchema" in tool for tool in tools)


def test_mcp_memory_round_trip() -> None:
    put_response = client.post(
        "/memory",
        json={"ticker": "AAPL", "content": "Previous Apple thesis", "metadata": {"source": "test"}},
    )
    assert put_response.status_code == 200

    search_response = client.post(
        "/memory/search",
        json={"ticker": "AAPL", "query": "Apple thesis", "top_k": 2},
    )
    assert search_response.status_code == 200
    payload = search_response.json()
    assert payload["result"]["items"]
