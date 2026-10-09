from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]
    call_id: str

class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    model: str
    tokens_used: int = 0
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate model response given chat history and optional tools."""
        pass
