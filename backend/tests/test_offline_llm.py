import pytest
from app.llm.offline_engine import OfflineDeterministicLLM
from app.llm.provider import ToolCall

@pytest.mark.asyncio
async def test_offline_llm_scripted_responses():
    llm = OfflineDeterministicLLM()
    llm.enqueue_simple_text("First scripted answer")
    llm.enqueue_tool_call("calculator", {"expr": "2+2"})

    resp1 = await llm.generate([{"role": "user", "content": "hello"}])
    assert resp1.content == "First scripted answer"
    assert len(resp1.tool_calls) == 0

    resp2 = await llm.generate([{"role": "user", "content": "calculate"}])
    assert len(resp2.tool_calls) == 1
    assert resp2.tool_calls[0].name == "calculator"
    assert resp2.tool_calls[0].arguments == {"expr": "2+2"}

@pytest.mark.asyncio
async def test_offline_llm_fault_injection():
    llm = OfflineDeterministicLLM()
    llm.set_fault_injection(error=RuntimeError("Simulated LLM Timeout"))

    with pytest.raises(RuntimeError, match="Simulated LLM Timeout"):
        await llm.generate([{"role": "user", "content": "test"}])

@pytest.mark.asyncio
async def test_offline_llm_adversarial():
    llm = OfflineDeterministicLLM()
    llm.set_fault_injection(adversarial=True)

    resp = await llm.generate([{"role": "user", "content": "do safe work"}])
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == "shell_exec"
    assert "cat /etc/passwd" in resp.tool_calls[0].arguments["command"]
