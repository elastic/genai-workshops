# backend/mcp_servers/elastic.py
from mcp import StdioServerParameters
from config import settings
from .base import MCPServerProcess
from . import register                   

params = StdioServerParameters(
    command="npx",
    args=["-y", "@elastic/mcp-server-elasticsearch"],
    env={"ES_URL": settings.ES_URL,
         "ES_API_KEY": settings.ES_API_KEY},
)

elastic_mcp = MCPServerProcess(params, tag="elastic-mcp")
register(elastic_mcp)                    
