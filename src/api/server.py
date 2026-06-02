import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import uvicorn
import logging

from src.agent.loop import AgentLoop
# Note: For production, DB manager, tools, etc. would be injected properly via dependency injection.

logger = logging.getLogger(__name__)

app = FastAPI(title="Intelligent Memory Engine API")

# Simple stateful loop instance for demonstration
_global_loop = AgentLoop()

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Standard REST endpoint for the reasoning loop.
    """
    try:
        response_text = await _global_loop.run(user_message=request.message)
        return ChatResponse(response=response_text)
    except Exception as e:
        logger.error(f"Chat REST error: {e}")
        return ChatResponse(response=f"Error processing chat: {e}")

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for bidirectional real-time memory interactions.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                message = parsed.get("message", "")
                
                # Execute reasoning
                response_text = await _global_loop.run(user_message=message)
                
                # Send result back
                await websocket.send_text(json.dumps({
                    "status": "success",
                    "response": response_text
                }))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": "Invalid JSON format."
                }))
    except WebSocketDisconnect:
        logger.info("Client disconnected from websocket.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
