import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import aiosqlite
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.models.chat import ChatRequest
from app.services.agent import get_compiled_graph

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Agent Chat"]
)

# We will construct the memory saver at runtime per-request
# because AsyncSqliteSaver.from_conn_string needs to run inside
# an async loop context.
# We no longer compile it globally here.

@router.post("")
async def chat_endpoint(request: ChatRequest):
    """
    Sends a message to the FlowPay LangGraph Agent.
    Streams back the response using Server-Sent Events (SSE).
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    
    async def event_generator():
        try:
            # Create an async database connection for the saver
            async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as memory:
                # Compile the graph with the saver bound for this thread/request
                agent = get_compiled_graph(memory)
                
                # We use astream_events to get granular updates on what the agent is doing
                # version "v2" is the recommended standard for LangChain/LangGraph >= 0.2
                async for event in agent.astream_events(
                    {"messages": [HumanMessage(content=request.message)]}, 
                    config, 
                    version="v2"
                ):
                    event_type = event["event"]
                    
                    # 1. When the Chatbot starts generating a response
                    if event_type == "on_chat_model_stream":
                        chunk = event["data"]["chunk"].content
                        if chunk:
                            yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"
                            
                    # 2. When the LLM decides to trigger a tool
                    elif event_type == "on_tool_start":
                        tool_name = event["name"]
                        yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name})}\n\n"
                    
                    # 3. When the tool finishes executing
                    elif event_type == "on_tool_end":
                        tool_name = event["name"]
                        # We could also yield the output if we wanted the frontend to see it
                        yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool_name})}\n\n"
                        
                # 4. End of stream
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    
        except Exception as e:
            logger.error(f"Error in agent stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
