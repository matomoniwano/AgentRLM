from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Literal
from rlm_service import chat_with_rlm

app = FastAPI(title="Agent RLM Backend")

# ----------------------------
# Request / Response models
# ----------------------------

class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    history: List[Message] = []
    message: str

class ChatResponse(BaseModel):
    text: str

# ----------------------------
# Routes
# ----------------------------

@app.get("/")
def health():
    return {"status": "ok", "agent": "RLM"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = chat_with_rlm(
        history=[m.dict() for m in req.history],
        message=req.message,
    )
    return {"text": reply}
