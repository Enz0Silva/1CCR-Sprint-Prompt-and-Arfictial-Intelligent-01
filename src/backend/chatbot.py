"""
ChargeGrid AI — Chatbot com Ollama API (cloud, via API key)
"""
import os
import requests

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "https://api.ollama.ai/v1/chat/completions")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "llama3")

with open("../../prompts/system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

def build_history() -> list:
    """Retorna histórico inicial com o system prompt."""
    return [{"role": "system", "content": SYSTEM_PROMPT}]

def chat(history: list, user_message: str) -> str:
    """
    Envia mensagem para a Ollama API e retorna a resposta.
    O histórico é atualizado in-place para manter contexto.
    """
    history.append({"role": "user", "content": user_message})

    response = requests.post(
        OLLAMA_API_URL,
        headers={
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": OLLAMA_MODEL,
            "messages": history
        },
        timeout=60
    )

    response.raise_for_status()
    reply = response.json()["choices"][0]["message"]["content"]
    history.append({"role": "assistant", "content": reply})
    return reply
