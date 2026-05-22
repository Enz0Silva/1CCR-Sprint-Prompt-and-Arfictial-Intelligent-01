"""
ChargeGrid AI — Chatbot com Groq API (gratuita)
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # lê do .env
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama3-8b-8192")

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(BASE_DIR, "..", "..", "prompts", "system_prompt.txt")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

def build_history() -> list:
    """Retorna histórico inicial com o system prompt."""
    return [{"role": "system", "content": SYSTEM_PROMPT}]

def chat(history: list, user_message: str) -> str:
    history.append({"role": "user", "content": user_message})

    response = requests.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": history,
            "temperature": 0.3
        },
        timeout=60
    )

    if not response.ok:
        print("Erro Groq:", response.status_code, response.text)
        response.raise_for_status()
    reply = response.json()["choices"][0]["message"]["content"]
    history.append({"role": "assistant", "content": reply})
    return reply