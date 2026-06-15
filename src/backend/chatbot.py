"""
ChargeGrid AI — Chatbot via Ollama Cloud
GoodWe EV Challenge 2026 | FIAP 1CCR Sprint 2
"""
import os
from dotenv import load_dotenv
from ollama import Client

load_dotenv()

OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "")
OLLAMA_MODEL   = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b")
OLLAMA_URL     = "https://ollama.com"

client = Client(
    host="https://ollama.com",
    headers={"Authorization": "Bearer " + OLLAMA_API_KEY}
)

print("API KEY carregada:", "OK" if OLLAMA_API_KEY else "FALTANDO — adicione OLLAMA_API_KEY no .env")

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(BASE_DIR, "..", "..", "prompts", "system_prompt.txt")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()


def build_history() -> list:
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def chat(history: list, user_message: str) -> str:
    history.append({"role": "user", "content": user_message})

    try:
        resposta = client.chat(
            model=OLLAMA_MODEL,
            messages=history,
            options={"num_predict": 1024, "temperature": 0.3},
            stream=False,
        )
        reply = resposta["message"]["content"].strip()
    except Exception as e:
        raise RuntimeError(f"Erro ao consultar Ollama Cloud: {e}")

    history.append({"role": "assistant", "content": reply})
    return reply


def reset_history() -> list:
    return build_history()