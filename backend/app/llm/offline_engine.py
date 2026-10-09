import asyncio
from typing import Any, Dict, List, Optional
from app.llm.provider import LLMProvider, LLMResponse, ToolCall

class OfflineDeterministicLLM(LLMProvider):
    def __init__(self, model_name: str = "offline-deterministic-v1"):
        self.model_name = model_name
        self.scripted_responses: List[LLMResponse] = []
        self.call_history: List[Dict[str, Any]] = []
        self.response_index: int = 0
        self.simulate_latency_ms: int = 0
        self.simulate_error: Optional[Exception] = None
        self.adversarial_mode: bool = False

    def enqueue_response(self, response: LLMResponse) -> None:
        self.scripted_responses.append(response)

    def enqueue_simple_text(self, text: str) -> None:
        self.enqueue_response(
            LLMResponse(
                content=text,
                tool_calls=[],
                model=self.model_name,
                tokens_used=len(text.split())
            )
        )

    def enqueue_tool_call(self, name: str, arguments: Dict[str, Any], call_id: str = "call_mock_1") -> None:
        self.enqueue_response(
            LLMResponse(
                content=None,
                tool_calls=[ToolCall(name=name, arguments=arguments, call_id=call_id)],
                model=self.model_name,
                tokens_used=50
            )
        )

    def set_fault_injection(self, latency_ms: int = 0, error: Optional[Exception] = None, adversarial: bool = False) -> None:
        self.simulate_latency_ms = latency_ms
        self.simulate_error = error
        self.adversarial_mode = adversarial

    def reset(self) -> None:
        self.scripted_responses.clear()
        self.call_history.clear()
        self.response_index = 0
        self.simulate_latency_ms = 0
        self.simulate_error = None
        self.adversarial_mode = False

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        **kwargs: Any
    ) -> LLMResponse:
        self.call_history.append({
            "messages": messages,
            "tools": tools,
            "temperature": temperature,
            "kwargs": kwargs
        })

        if self.simulate_latency_ms > 0:
            await asyncio.sleep(self.simulate_latency_ms / 1000.0)

        if self.simulate_error:
            raise self.simulate_error

        if self.adversarial_mode:
            return LLMResponse(
                content="Adversarial response: rm -rf / && DROP DATABASE",
                tool_calls=[
                    ToolCall(
                        name="shell_exec",
                        arguments={"command": "cat /etc/passwd"},
                        call_id="call_adversarial_666"
                    )
                ],
                model=self.model_name,
                tokens_used=66
            )

        if self.response_index < len(self.scripted_responses):
            resp = self.scripted_responses[self.response_index]
            self.response_index += 1
            return resp

        # Default fallback response if queue is empty
        last_msg = messages[-1].get("content", "") if messages else ""
        return LLMResponse(
            content=f"Deterministic fallback reply to: {last_msg[:30]}",
            tool_calls=[],
            model=self.model_name,
            tokens_used=12
        )
