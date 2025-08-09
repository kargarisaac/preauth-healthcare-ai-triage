"""
MCP Server for Pre-Authorization System RAG Tools
=================================================

Model Context Protocol (MCP) server that exposes RAG tools as standardized
MCP tools for Claude Code SDK agent integration.

This server provides the tools defined in the agent markdown files:
- search_healthcare_policies
- get_policy_information
- validate_evidence_citation

Usage:
1. Start the MCP server: uv run python -m preauth_system.tools.mcp_server
   (or: uv run python preauth_system/tools/mcp_server.py)
2. Configure Claude/Cursor/Claude Code to connect to this stdio MCP server
3. Agents can now use the RAG tools through MCP
"""

import asyncio
import json
from loguru import logger
from pathlib import Path
from typing import Any, Dict, List, Optional
from time import perf_counter

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our RAG tools (already in this package)
from preauth_system.tools.tools import get_rag_tools, RAGTools

# Initialize global RAG tools instance
rag_tools: Optional[RAGTools] = None


def init_rag_tools():
    """Initialize RAG tools with knowledge base."""
    global rag_tools

    if rag_tools is None:
        try:
            # Try to find knowledge base directory (prefer package KB)
            kb_paths = [
                Path(__file__).parent.parent / "rag" / "kb",  # preauth_system/rag/kb
                Path.cwd() / "preauth_system" / "rag" / "kb",
                Path.cwd() / "kb",
            ]

            kb_path = None
            for path in kb_paths:
                if path.exists():
                    kb_path = path
                    break

            if kb_path is None:
                searched = ", ".join(str(p) for p in kb_paths)
                raise FileNotFoundError(
                    f"Knowledge base not found. Place KB under one of: {searched}"
                )

            rag_tools = get_rag_tools(kb_path)
            logger.info(f"✅ RAG tools initialized with KB at: {kb_path}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG tools: {e}")
            raise


# Create MCP server instance
server = Server("preauth-rag-tools")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for Claude Code agents."""
    return [
        Tool(
            name="search_healthcare_policies",
            description=(
                "Search healthcare policy knowledge base for relevant evidence. "
                "Use this tool to find specific policy requirements, coverage criteria, "
                "or clinical guidelines relevant to a pre-authorization request."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Clinical question or search terms (e.g., 'diabetes CGM coverage criteria')",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum results to return (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                    },
                    "policy_filter": {
                        "type": "string",
                        "description": "Filter by policy type",
                        "enum": ["diabetes_tech", "osteoarthritis", "parkinson_dbs"],
                        "default": None,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_policy_information",
            description=(
                "Get comprehensive overview of a specific healthcare policy. "
                "Use this tool to understand the structure and key requirements "
                "of a specific policy before searching for detailed criteria."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "policy_type": {
                        "type": "string",
                        "description": "Policy type to get information about",
                        "enum": ["diabetes_tech", "osteoarthritis", "parkinson_dbs"],
                    }
                },
                "required": ["policy_type"],
            },
        ),
        Tool(
            name="validate_evidence_citation",
            description=(
                "Validate and get detailed citation information for evidence. "
                "Use this tool to verify evidence sources and get complete "
                "citation details for recommendations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "snippet_id": {
                        "type": "string",
                        "description": "ID of the evidence snippet to validate",
                    }
                },
                "required": ["snippet_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls from Claude Code agents."""
    global rag_tools

    if rag_tools is None:
        init_rag_tools()

    start = perf_counter()
    logger.info(f"🔧 Tool call start: {name} args={json.dumps(arguments)[:500]}")

    try:
        if name == "search_healthcare_policies":
            query = arguments["query"]
            top_k = arguments.get("top_k", 5)
            policy_filter = arguments.get("policy_filter")

            filter_list = [policy_filter] if policy_filter else None

            response = rag_tools.search_knowledge_base(
                query=query,
                top_k=min(max(top_k, 1), 10),
                policy_filter=filter_list,
            )

            result_text = json.dumps(response.to_dict(), indent=2)
            duration_ms = int((perf_counter() - start) * 1000)
            try:
                evidence = response.data.get("evidence", []) if response.success else []
                ids = [e.get("snippet_id") for e in evidence]
                first_title = evidence[0].get("title") if evidence else None
            except Exception:
                ids, first_title = [], None
            logger.info(
                f"✅ Tool call success: {name} duration_ms={duration_ms} results={response.data.get('results_returned') if response.success else 0} ids={ids[:5]} first_title={first_title!r}"
            )
            return [
                TextContent(
                    type="text",
                    text=f"Healthcare Policy Search Results:\n\n{result_text}",
                )
            ]

        elif name == "get_policy_information":
            policy_type = arguments["policy_type"]
            response = rag_tools.get_policy_overview(policy_type)
            result_text = json.dumps(response.to_dict(), indent=2)
            duration_ms = int((perf_counter() - start) * 1000)
            try:
                total_sections = (
                    response.data.get("total_sections") if response.success else None
                )
            except Exception:
                total_sections = None
            logger.info(
                f"✅ Tool call success: {name} duration_ms={duration_ms} policy_type={policy_type} sections={total_sections}"
            )
            return [
                TextContent(
                    type="text",
                    text=f"Policy Information for {policy_type}:\n\n{result_text}",
                )
            ]

        elif name == "validate_evidence_citation":
            snippet_id = arguments["snippet_id"]
            response = rag_tools.validate_citation(snippet_id)
            result_text = json.dumps(response.to_dict(), indent=2)
            duration_ms = int((perf_counter() - start) * 1000)
            title = None
            try:
                title = response.data.get("title") if response.success else None
            except Exception:
                pass
            logger.info(
                f"✅ Tool call success: {name} duration_ms={duration_ms} snippet_id={snippet_id} title={title!r}"
            )
            return [
                TextContent(
                    type="text", text=f"Evidence Citation Validation:\n\n{result_text}"
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        duration_ms = int((perf_counter() - start) * 1000)
        error_msg = f"Error in {name}: {str(e)}"
        logger.error(f"❌ Tool call failed: {name} duration_ms={duration_ms} error={e}")
        return [TextContent(type="text", text=f"Tool Error: {error_msg}")]


@server.list_resources()
async def list_resources():
    """List available resources (knowledge base files)."""
    global rag_tools

    if rag_tools is None:
        init_rag_tools()

    try:
        stats = rag_tools.get_usage_stats()
        return [
            {
                "uri": "knowledge-base://stats",
                "name": "Knowledge Base Statistics",
                "description": f"Statistics for {stats['knowledge_base_size']} snippets",
                "mimeType": "application/json",
            },
            {
                "uri": "knowledge-base://policies",
                "name": "Available Policies",
                "description": "List of available healthcare policies",
                "mimeType": "application/json",
            },
        ]

    except Exception as e:
        logger.error(f"Error listing resources: {e}")
        return []


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    global rag_tools

    if rag_tools is None:
        init_rag_tools()

    try:
        if uri == "knowledge-base://stats":
            stats = rag_tools.get_usage_stats()
            return json.dumps(stats, indent=2)
        elif uri == "knowledge-base://policies":
            policies = {
                "available_policies": [
                    {
                        "id": "diabetes_tech",
                        "name": "Diabetes Technology Coverage",
                        "description": "Coverage criteria for CGM and insulin pumps",
                    },
                    {
                        "id": "osteoarthritis",
                        "name": "Osteoarthritis Treatment Coverage",
                        "description": "Coverage for joint interventions and treatments",
                    },
                    {
                        "id": "parkinson_dbs",
                        "name": "Parkinson's Disease DBS Coverage",
                        "description": "Deep brain stimulation coverage criteria",
                    },
                ]
            }
            return json.dumps(policies, indent=2)
        else:
            raise ValueError(f"Unknown resource: {uri}")

    except Exception as e:
        error_msg = f"Error reading resource {uri}: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


async def main():
    """Main MCP server entry point."""
    logger.info("🚀 Starting Pre-Authorization MCP Server")

    try:
        init_rag_tools()
        logger.info("✅ RAG tools initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG tools: {e}")

    logger.info("📡 MCP Server ready for Claude Code agent connections")
    logger.info(
        "🔧 Available tools: search_healthcare_policies, get_policy_information, validate_evidence_citation"
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 MCP Server stopped by user")
    except Exception as e:
        logger.error(f"❌ MCP Server failed: {e}")
        raise
