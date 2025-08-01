from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        print(f"Received: {data}")
        if data.startswith("heartbeat:"):
            counter = data.split(":")[1]
            await websocket.send_text(f"ack:{counter}")
        else:
            await websocket.send_text("echo: " + data)