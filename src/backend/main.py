"""
ChargeGrid AI — Backend FastAPI
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.backend.chatbot import build_history, chat

app = FastAPI(title="ChargeGrid AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    global conversation_history
    conversation_history = build_history()
    return {"status": "histórico resetado"}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": os.getenv("GROQ_MODEL", "llama3-8b-8192"),
        "api_url": os.getenv("GROQ_API_URL", "")
    }