from fastapi import FastAPI, WebSocket
from handleRequest import build_faq_prompt, setApiKey, setFaqIntents
import traceback
import json

app = FastAPI()

def make_response(response_type: str, data) -> str:
    return json.dumps({
        "type": response_type,
        "data": data
    })

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()

            print(f"Received: {message}")

            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send_text(make_response("error", "Invalid JSON"))
                continue
            message_type = data.get("type")

            if message_type == "api":
                setApiKey(data.get("apiKey"))
                setFaqIntents()
                await websocket.send_text(make_response("api", "API key set successfully"))
                

            elif message_type == "prompt":
                result = await build_faq_prompt(data["userTranscript"], data["fullTranscription"],data["smallTalkHistory"])
                await websocket.send_text(make_response("prompt", result))

            elif message_type == "heartbeat":
                counter = data.get("counter", "")
                await websocket.send_text(make_response("heartbeat", f"ack:{counter}"))

            else:
                await websocket.send_text(make_response("echo", data))

    except Exception as e:
        print("Client disconnected")
        traceback.print_exc()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=True)