# test_mcp_connection.py
import pytest
from fastmcp import Client
import pytest_asyncio
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.client.auth import BearerAuth
import os
from dotenv import load_dotenv
load_dotenv(override=True)

@pytest_asyncio.fixture
async def mcp_client():
    """Fixture to create an MCP client connected to the server."""
    transport = StreamableHttpTransport(
    url="http://localhost:8000/mcp",
    headers={
        "Authorization": "Bearer " + os.getenv("ASTRA_MCP_SERVER_TOKEN")
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
async def test_run_search_airline_tickets(mcp_client):
    """Test running the search_products tool through the MCP client."""
    result = await mcp_client.call_tool("search_airline_tickets", {"customer_id": "dc3a050c-0eb5-42dd-ab4f-450f0819c8e4"})
    print(result)
    assert result is not None, "Server did not respond with search_airline_tickets tool"
    assert result.documents is not None, "Server did not respond with search_products tool"
    