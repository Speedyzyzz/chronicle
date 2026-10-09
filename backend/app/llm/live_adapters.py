import os
import httpx
from typing import Any, Dict, List, Optional
from app.llm.provider import LLMProvider, LLMResponse, ToolCall
from app.config import settings

class OpenAIAdapter(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.model = model

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        **kwargs: Any
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]["message"]
        tool_calls = []
        if "tool_calls" in choice and choice["tool_calls"]:
            import json
            for tc in choice["tool_calls"]:
                tool_calls.append(
                    ToolCall(
                        name=tc["function"]["name"],
                        arguments=json.loads(tc["function"]["arguments"]),
                        call_id=tc["id"]
                    )
                )

        return LLMResponse(
            content=choice.get("content"),
            tool_calls=tool_calls,
            model=data.get("model", self.model),
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            raw_metadata=data
        )

class AnthropicAdapter(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
        self.model = model

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        **kwargs: Any
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not configured.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        # Format messages for Anthropic
        system_msg = ""
        user_msgs = []
        for m in messages:
            if m.get("role") == "system":
                system_msg = m.get("content", "")
            else:
                user_msgs.append(m)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": user_msgs,
            "temperature": temperature,
            "max_tokens": 4096
        }
        if system_msg:
            payload["system"] = system_msg
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content_parts = []
        tool_calls = []
        for block in data.get("content", []):
            if block["type"] == "text":
                content_parts.append(block["text"])
            elif block["type"] == "tool_use":
                tool_calls.append(
                    ToolCall(
                        name=block["name"],
                        arguments=block.get("input", {}),
                        call_id=block["id"]
                    )
                )

        return LLMResponse(
            content="".join(content_parts) if content_parts else None,
            tool_calls=tool_calls,
            model=data.get("model", self.model),
            tokens_used=data.get("usage", {}).get("output_tokens", 0),
            raw_metadata=data
        )

class GeminiAdapter(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-pro"):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        self.model = model

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        **kwargs: Any
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        # Simplified normalized request
        contents = []
        for m in messages:
            role = "user" if m.get("role") in ["user", "system"] else "model"
            contents.append({"role": role, "parts": [{"text": str(m.get("content", ""))}]})

        payload = {"contents": contents, "generationConfig": {"temperature": temperature}}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidate = data.get("candidates", [{}])[0]
        text_parts = [p.get("text", "") for p in candidate.get("content", {}).get("parts", [])]

        return LLMResponse(
            content="".join(text_parts),
            tool_calls=[],
            model=self.model,
            tokens_used=data.get("usageMetadata", {}).get("totalTokenCount", 0),
            raw_metadata=data
        )
