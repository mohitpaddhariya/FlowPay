from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's natural language input.")
    thread_id: str = Field(default="default", description="The conversation thread ID for LangGraph memory persistence.")
