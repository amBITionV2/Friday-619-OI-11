# ==========================================================
#  SERVER.PY — Robust WebSocket Server for FRIDAY1 & FRIDAY2
# ==========================================================
import asyncio
import websockets
import json

connected_clients = {}  # {"Friday1": websocket, "Friday2": websocket}

async def handle_client(websocket, path):
    client_name = None
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Invalid JSON"}))
                continue

            action = data.get("action")

            # ---------------- Register Client ----------------
            if action == "register":
                client_name = data.get("name")
                connected_clients[client_name] = websocket
                print(f"[+] {client_name} connected")
                await websocket.send(json.dumps({"status": "registered"}))
                continue

            # ---------------- Relay Message ----------------
            elif action == "message":
                target = data.get("to")
                sender = data.get("from")
                text = data.get("text")

                if target in connected_clients:
                    try:
                        await connected_clients[target].send(json.dumps({
                            "from": sender,
                            "type": "message",
                            "text": text
                        }))
                        print(f"📤 {sender} → {target}: {text}")
                    except Exception as e:
                        print(f"⚠️ Error sending message to {target}: {e}")
                        await websocket.send(json.dumps({"error": f"Could not send to {target}"}))
                else:
                    await websocket.send(json.dumps({"error": f"{target} not online"}))

    except websockets.ConnectionClosedOK:
        print(f"[-] {client_name} disconnected gracefully")
    except websockets.ConnectionClosedError:
        print(f"[-] {client_name} disconnected with error")
    except Exception as e:
        print(f"⚠️ Unexpected error with {client_name}: {e}")
    finally:
        if client_name and client_name in connected_clients:
            del connected_clients[client_name]
            print(f"ℹ️ {client_name} removed from connected clients")

async def main():
    host = "0.0.0.0"     # listen on all interfaces
    port = 8765
    async with websockets.serve(handle_client, host, port, ping_timeout=None, ping_interval=None):
        print(f"🌐 Server running on ws://{host}:{port}")
        await asyncio.Future()  # Keep server alive

if __name__ == "__main__":
    asyncio.run(main()) 
