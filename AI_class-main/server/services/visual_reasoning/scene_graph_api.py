from typing import Dict, Any, List, Optional

# Import functions directly from the new graph_service
from server.services.visual_reasoning.graph_service import (
    build_graph_data,
    add_new_entity,
    add_new_relation,
)
from server.services.visual_reasoning.Q_Process import QuestionProcessor

async def get_current_scene_graph_state(session_id: str) -> Dict[str, Any]:
    """Fetches the current state of the scene graph by calling the service directly."""
    try:
        graph_data = build_graph_data(session_id)
        return {
            "status": "success",
            "graph_data": graph_data,
            "node_count": len(graph_data.get("nodes", [])),
            "edge_count": len(graph_data.get("edges", [])),
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get graph state: {e}"}

async def query_node_with_hidden_attributes(node_name: str, graph: object) -> Optional[str]:
    """Queries for node details, including hidden attributes, by direct function call."""
    try:
        processor = QuestionProcessor(graph=graph)
        details = processor._get_node_details_from_graph(node_name)
        if details.get("found"):
            return "\n".join(details.get("relationships", []))
        return None
    except Exception:
        return None

async def add_entity_function(session_id: str, entity: Dict[str, Any]) -> Dict[str, Any]:
    """Adds an entity to the graph by calling the service directly."""
    try:
        return add_new_entity(
            session_id, 
            source=entity.get("source"), 
            relationship=entity.get("relationship"), 
            target=entity.get("target")
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def add_relationship_function(session_id: str, relationship: Dict[str, Any]) -> Dict[str, Any]:
    """Adds a relationship to the graph by calling the service directly."""
    try:
        return add_new_relation(
            session_id,
            source=relationship.get("source"),
            target=relationship.get("target"),
            relationship=relationship.get("relationship")
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}
