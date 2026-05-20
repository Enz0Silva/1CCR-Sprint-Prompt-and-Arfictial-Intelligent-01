"""
ChargeGrid AI — Backend FastAPI
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import build_history, chat

app = FastAPI(title="ChargeGrid AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Histórico de conversa em memória (por sessão simples)
conversation_history = build_history()

class Message(BaseModel):
    text: str

@app.post("/chat")
async def chat_endpoint(msg: Message):
    try:
        response = chat(conversation_history, msg.text)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
async def reset_chat():
    """Reinicia o histórico de conversa."""
    global conversation_history
    conversation_history = build_history()
    return {"status": "histórico resetado"}

@app.get("/health")
async def health():
    import os
    return {
        "status": "ok",
        "model": os.getenv("OLLAMA_MODEL", "llama3"),
        "api_url": os.getenv("OLLAMA_API_URL", "")
    }
