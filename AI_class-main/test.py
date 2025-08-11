import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse  # Used to serve the frontend page
import networkx as nx

# --- 1. Initialize application and graph structure ---
app = FastAPI()
# Use DiGraph because relationships are usually directed (e.g., "cat" -> "sits on" -> "mat")
G = nx.DiGraph()


# Manages all active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # This print statement goes to the server console, not the client WebSocket
        print(f"New client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        # This print statement goes to the server console, not the client WebSocket
        print(f"Client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        # These print statements go to the server console, not the client WebSocket
        print(f"Broadcasting to {len(self.active_connections)} client(s).")
        print(f"Message: {message}")
        for connection in self.active_connections:
            # Ensure only JSON messages are sent here
            await connection.send_text(message)

manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # After successful connection, immediately send the initial graph data in JSON format
    # IMPORTANT: DO NOT send any other non-JSON text directly from the WebSocket endpoint.
    initial_graph_data = nx.node_link_data(G)
    await websocket.send_text(json.dumps({"type": "full_graph", "data": initial_graph_data}))

    try:
        # Loop indefinitely to keep the connection open and listen for disconnect events
        while True:
            # We are not expecting messages from the client in this setup,
            # but this line keeps the connection alive and catches disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("A client disconnected.")

# --- 3. HTTP endpoint for dynamically adding relationships ---
# This is where you would receive LLM analysis results
@app.post("/add-relation")
async def add_relation(source: str, target: str, relation: str):
    """
    Receives a new relationship and updates the graph.
    For example: source='Cat', target='Mat', relation='sits_on'
    """
    # **DEBUGGING LINE ADDED HERE**
    print(f"Received add-relation request: source='{source}', target='{target}', relation='{relation}'")

    # Add nodes (networkx automatically ignores if they already exist)
    G.add_node(source, label=source)
    G.add_node(target, label=target)
    # Add an edge with a label
    G.add_edge(source, target, label=relation)

    # Prepare the update information to be broadcasted
    update_data = {
        "type": "update",
        "data": {
            "source": {"id": source, "label": source},
            "target": {"id": target, "label": target},
            "edge": {"source": source, "target": target, "label": relation}
        }
    }

    # Broadcast this update via WebSocket
    # Ensure this message is always a JSON string
    await manager.broadcast(json.dumps(update_data))

    return {"status": "success", "message": "Relation added and broadcasted."}


# --- 4. Endpoint to serve the frontend page (for demonstration purposes) ---
@app.get("/")
async def get():
    # This part can be served directly from an HTML file for convenience
    # Make sure 'index.html' (or 'test.html' based on your file name) exists in the same directory
    with open("test.html", "r", encoding="utf-8") as f: # Ensure encoding is utf-8
        return HTMLResponse(f.read())
