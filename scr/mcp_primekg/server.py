"""
MCP Server for Harvard PrimeKG Knowledge Graph
Provides tools to query and explore the PrimeKG precision medicine knowledge graph.
"""

import os
import logging
from typing import Any
from pathlib import Path

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .primekg_client import PrimeKGClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-primekg")

# Get configuration from environment
DATA_PATH = os.getenv("PRIMEKG_DATA_PATH", str(Path.home() / "primekg_data"))
AUTO_UPDATE = os.getenv("PRIMEKG_AUTO_UPDATE", "true").lower() == "true"
UPDATE_INTERVAL_DAYS = int(os.getenv("PRIMEKG_UPDATE_INTERVAL_DAYS", "7"))
INSTRUCTIONS = os.getenv("INSTRUCTIONS", 
    "Query the PrimeKG knowledge graph for precision medicine insights, including drug-disease-gene relationships.")

# Initialize server
server = Server("mcp-primekg")

# Initialize PrimeKG client with auto-update
primekg_client = PrimeKGClient(
    data_path=DATA_PATH,
    auto_update=AUTO_UPDATE,
    update_interval_days=UPDATE_INTERVAL_DAYS
)


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available PrimeKG resources."""
    return [
        Resource(
            uri="primekg://schema",
            name="PrimeKG Schema",
            description="Schema and structure of the PrimeKG knowledge graph",
            mimeType="text/plain",
        ),
        Resource(
            uri="primekg://statistics",
            name="PrimeKG Statistics",
            description="Statistics about nodes and relationships in PrimeKG",
            mimeType="text/plain",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a PrimeKG resource."""
    if uri == "primekg://schema":
        return primekg_client.get_schema()
    elif uri == "primekg://statistics":
        return primekg_client.get_statistics()
    else:
        raise ValueError(f"Unknown resource: {uri}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available PrimeKG query tools."""
    return [
        Tool(
            name="search_nodes",
            description="Search for nodes in PrimeKG by name or ID. Returns nodes with their type and properties.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (gene name, drug name, disease name, etc.)",
                    },
                    "node_type": {
                        "type": "string",
                        "description": "Filter by node type (e.g., 'gene', 'drug', 'disease', 'biological_process')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_node_relationships",
            description="Get all relationships for a specific node in PrimeKG",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Node ID or name",
                    },
                    "relationship_type": {
                        "type": "string",
                        "description": "Filter by relationship type (optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of relationships to return",
                        "default": 50,
                    },
                },
                "required": ["node_id"],
            },
        ),
        Tool(
            name="find_drug_targets",
            description="Find gene/protein targets for a given drug",
            inputSchema={
                "type": "object",
                "properties": {
                    "drug_name": {
                        "type": "string",
                        "description": "Name of the drug",
                    },
                },
                "required": ["drug_name"],
            },
        ),
        Tool(
            name="find_disease_genes",
            description="Find genes associated with a disease",
            inputSchema={
                "type": "object",
                "properties": {
                    "disease_name": {
                        "type": "string",
                        "description": "Name of the disease",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of genes to return",
                        "default": 50,
                    },
                },
                "required": ["disease_name"],
            },
        ),
        Tool(
            name="find_drug_disease_paths",
            description="Find potential drug-disease connections through genes/proteins",
            inputSchema={
                "type": "object",
                "properties": {
                    "drug_name": {
                        "type": "string",
                        "description": "Name of the drug",
                    },
                    "disease_name": {
                        "type": "string",
                        "description": "Name of the disease",
                    },
                    "max_path_length": {
                        "type": "integer",
                        "description": "Maximum length of connection path",
                        "default": 3,
                    },
                },
                "required": ["drug_name", "disease_name"],
            },
        ),
        Tool(
            name="get_node_details",
            description="Get detailed information about a specific node",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Node ID or name",
                    },
                },
                "required": ["node_id"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls for PrimeKG queries."""
    try:
        if name == "search_nodes":
            result = primekg_client.search_nodes(
                query=arguments["query"],
                node_type=arguments.get("node_type"),
                limit=arguments.get("limit", 10),
            )
        elif name == "get_node_relationships":
            result = primekg_client.get_node_relationships(
                node_id=arguments["node_id"],
                relationship_type=arguments.get("relationship_type"),
                limit=arguments.get("limit", 50),
            )
        elif name == "find_drug_targets":
            result = primekg_client.find_drug_targets(
                drug_name=arguments["drug_name"]
            )
        elif name == "find_disease_genes":
            result = primekg_client.find_disease_genes(
                disease_name=arguments["disease_name"],
                limit=arguments.get("limit", 50),
            )
        elif name == "find_drug_disease_paths":
            result = primekg_client.find_drug_disease_paths(
                drug_name=arguments["drug_name"],
                disease_name=arguments["disease_name"],
                max_path_length=arguments.get("max_path_length", 3),
            )
        elif name == "get_node_details":
            result = primekg_client.get_node_details(
                node_id=arguments["node_id"]
            )
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=str(result))]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-primekg",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
