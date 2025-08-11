import redis
import json
import networkx as nx
from networkx.readwrite import json_graph
from typing import Dict, Any, List, Optional

# --- Redis Connection Setup ---
# For production, use a more robust configuration management system.
try:
    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("✅ Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"⚠️ Redis connection failed: {e}. The visual reasoning module will not work correctly.")
    redis_client = None

# --- Helper Functions for Serialization ---

def serialize_graph(graph: nx.DiGraph) -> str:
    """Serializes a NetworkX graph to a JSON string."""
    return json.dumps(json_graph.node_link_data(graph))

def deserialize_graph(graph_str: str) -> nx.DiGraph:
    """Deserializes a JSON string to a NetworkX graph."""
    if not graph_str:
        return nx.DiGraph()
    data = json.loads(graph_str)
    return json_graph.node_link_graph(data)

# --- State Management Functions ---

def get_session_key(session_id: str) -> str:
    """Generates the Redis key for a given session."""
    return f"session:{session_id}"

def get_session_data(session_id: str) -> Dict[str, Any]:
    """Retrieves all data for a given session from Redis."""
    if not redis_client:
        return {}
    session_key = get_session_key(session_id)
    data = redis_client.hgetall(session_key)
    return data

def get_graph(session_id: str) -> nx.DiGraph:
    """Retrieves the graph for a session."""
    data = get_session_data(session_id)
    graph_str = data.get("graph", "")
    return deserialize_graph(graph_str)

def set_graph(session_id: str, graph: nx.DiGraph):
    """Saves the graph for a session."""
    if not redis_client:
        return
    session_key = get_session_key(session_id)
    redis_client.hset(session_key, "graph", serialize_graph(graph))

def get_hidden_attributes(session_id: str) -> List[Dict[str, Any]]:
    """Retrieves hidden attributes for a session."""
    data = get_session_data(session_id)
    attributes_str = data.get("hidden_attributes", "[]")
    return json.loads(attributes_str)

def set_hidden_attributes(session_id: str, attributes: List[Dict[str, Any]]):
    """Saves hidden attributes for a session."""
    if not redis_client:
        return
    session_key = get_session_key(session_id)
    redis_client.hset(session_key, "hidden_attributes", json.dumps(attributes))

def get_current_image(session_id: str) -> Optional[bytes]:
    """Retrieves the current image for a session."""
    if not redis_client:
        return None
    session_key = get_session_key(session_id)
    # Note: Storing large binary data like images in Redis is not always ideal.
    # A better approach might be saving to a file store (like MinIO/S3) and storing the URL/path in Redis.
    # For now, we retrieve it directly, assuming it's stored as bytes.
    # The `decode_responses=True` might affect this, so we use a separate client for bytes.
    redis_byte_client = redis.StrictRedis(host='localhost', port=6379, db=0)
    image_bytes = redis_byte_client.hget(session_key, "current_image")
    return image_bytes

def set_current_image(session_id: str, image_bytes: bytes):
    """Saves the current image for a session."""
    if not redis_client:
        return
    session_key = get_session_key(session_id)
    redis_byte_client = redis.StrictRedis(host='localhost', port=6379, db=0)
    redis_byte_client.hset(session_key, "current_image", image_bytes)

def clear_session_state(session_id: str):
    """Deletes all data for a specific session."""
    if not redis_client:
        return
    session_key = get_session_key(session_id)
    redis_client.delete(session_key)

# The old app_state is now obsolete.
# app_state: Dict[str, Any] = { ... }
