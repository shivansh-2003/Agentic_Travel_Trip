#!/usr/bin/env python3
"""
Combined MCP Server
Combines multiple MCP servers including hotel booking, echo, and math servers.
"""

import contextlib
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse


from hotels import mcp as hotel_mcp
from flight_search import mcp as flight_mcp
from travel import mcp as travel_mcp
# Create a combined lifespan to manage all session managers
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(hotel_mcp.session_manager.run())
        await stack.enter_async_context(flight_mcp.session_manager.run())
        await stack.enter_async_context(travel_mcp.session_manager.run())
        yield

# Create FastAPI app with lifespan
app = FastAPI(
    title="Combined MCP Server",
    lifespan=lifespan
)




app.mount("/hotels", hotel_mcp.streamable_http_app())
print("✅ Hotel booking server mounted at /hotels")

app.mount("/flight", flight_mcp.streamable_http_app())
print("✅ Flight search server mounted at /flight")

app.mount("/travel", travel_mcp.streamable_http_app())
print("✅ Travel server mounted at /travel")

# Get port from environment or default to 10000
PORT = 8000

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=PORT,
       
    )