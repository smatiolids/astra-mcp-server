# test_mcp_connection.py
import pytest
from fastmcp import Client
import pytest_asyncio
from fastmcp.client.transports import StreamableHttpTransport
import os
from dotenv import load_dotenv
load_dotenv(override=True)

@pytest_asyncio.fixture
async def mcp_client():
    """Fixture to create an MCP client connected to the server."""
    transport = StreamableHttpTransport(
    url="http://localhost:8000/mcp",
    headers={
        "Authorization": "Bearer " + (os.getenv("AGENTIC_ASTRA_TOKEN") or os.getenv("ASTRA_MCP_SERVER_TOKEN"))
        }
    )
    
    client = Client(transport)
    async with client:
        yield client

@pytest.mark.asyncio
async def test_server_connection(mcp_client):
    """Test that the MCP client can successfully ping the server."""
    response = await mcp_client.ping()  # assuming the client has a ping method
    assert response == True, "Server did not respond with 'ok'"

@pytest.mark.asyncio
async def test_list_tools(mcp_client):
    """Test listing tools through the MCP client."""
    result = await mcp_client.list_tools()
    print(result)
    assert result is not None, "Server did not respond with tools"
    assert len(result) > 0, "Server did not respond with tools"

@pytest.mark.asyncio
async def test_run_search_products(mcp_client):
    """Test running the search_products tool through the MCP client."""
    result = await mcp_client.call_tool("search_products", {"search_query": "blue pants", "max_price": 500})
    print(result)
    assert result is not None, "Server did not respond with search_products tool"
    
@pytest.mark.asyncio
async def test_run_rag(mcp_client):
    """Test running the search_products tool through the MCP client."""
    result = await mcp_client.call_tool("rag_latam_airlines", {"search_query": "posso remarcar uma passagem?"})
    print(result)
    assert result is not None, "Server did not respond with rag tool"

@pytest.mark.asyncio
async def test_run_list_collections(mcp_client):
    """Test running the search_products tool through the MCP client."""
    result = await mcp_client.call_tool("collections", {})
    print(result)
    assert result is not None, "Server did not respond with collections tool"