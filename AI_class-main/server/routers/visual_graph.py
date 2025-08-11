from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from typing import Dict, Any

import networkx as nx

from server.services.visual_reasoning.caption import miscellaneous_analysis
from server.services.visual_reasoning.state import (
    set_graph,
    set_hidden_attributes,
    set_current_image,
    clear_session_state,
)
from server.services.visual_reasoning.graph_service import *
import uuid

router = APIRouter()

@router.post("/parse_image")
async def parse_image(file: UploadFile = File(...), session_id: str = Body(None)):
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    sid = session_id or str(uuid.uuid4())
    clear_session_state(sid)
    
    graph = nx.DiGraph()
    set_graph(sid, graph)

    try:
        image_content = await file.read()
        set_current_image(sid, image_content)
        
        graph_data_from_ai = await miscellaneous_analysis(image_content)
        
        if "error" in graph_data_from_ai or "nodes" not in graph_data_from_ai:
            return build_graph_data(sid)

        for node in graph_data_from_ai.get("nodes", []):
            graph.add_node(node["id"], **{k: v for k, v in node.items() if k != 'id'})

        for edge in graph_data_from_ai.get("edges", []):
            graph.add_edge(edge["source"], edge["target"], relation=edge["relationship"])

        set_hidden_attributes(sid, graph_data_from_ai.get("hidden_attributes", []))
        set_graph(sid, graph)
        
        return build_graph_data(sid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing image: {e}")

@router.post("/add_entity")
async def add_entity_endpoint(payload: Dict[str, str] = Body(...)):
    sid = payload.get("session_id")
    if not sid: raise HTTPException(status_code=400, detail="session_id is required.")
    source, rel, target = payload.get("source_name"), payload.get("relationship"), payload.get("target_name")
    if not all([source, rel, target]):
        raise HTTPException(status_code=400, detail="Missing required fields.")
    return add_new_entity(sid, source, rel, target)

@router.post("/add_node")
async def add_node_endpoint(payload: Dict[str, Any] = Body(...)):
    sid = payload.get("session_id")
    if not sid: raise HTTPException(status_code=400, detail="session_id is required.")
    try:
        return add_new_node(sid, payload["id"], payload["type"], payload["level"])
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/add_relation")
async def add_relation_endpoint(payload: Dict[str, str] = Body(...)):
    sid = payload.get("session_id")
    if not sid: raise HTTPException(status_code=400, detail="session_id is required.")
    try:
        return add_new_relation(sid, payload["source"], payload["target"], payload["relationship"])
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update_node")
async def update_node_endpoint(payload: Dict[str, Any] = Body(...)):
    sid = payload.get("session_id")
    if not sid: raise HTTPException(status_code=400, detail="session_id is required.")
    try:
        old_id = payload.get("old_id") or payload.get("id")
        return update_existing_node(sid, old_id, payload["id"], payload["type"], payload["level"])
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update_relation")
async def update_relation_endpoint(payload: Dict[str, Any] = Body(...)):
    sid = payload.get("session_id")
    if not sid: raise HTTPException(status_code=400, detail="session_id is required.")
    try:
        return update_existing_relation(sid, payload["index"], payload["source"], payload["target"], payload["relationship"])
    except (ValueError, IndexError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/add_attribute")
async def add_attribute_endpoint(payload: Dict[str, Any] = Body(...)):
    sid = payload.get("session_id")
    if not sid: raise HTTPException(status_code=400, detail="session_id is required.")
    try:
        return add_new_attribute(sid, payload["entity_id"], payload["attribute_type"], payload["attribute_value"])
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update_attribute")
async def update_attribute_endpoint(payload: Dict[str, Any] = Body(...)):
    sid = payload.get("session_id")
    if not sid: raise HTTPException(status_code=400, detail="session_id is required.")
    try:
        return update_existing_attribute(sid, payload["index"], payload["entity_id"], payload["attribute_type"], payload["attribute_value"])
    except (ValueError, IndexError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/delete_node")
async def delete_node_endpoint(payload: Dict[str, str] = Body(...)):
    sid = payload.get("session_id")
    if not sid: raise HTTPException(status_code=400, detail="session_id is required.")
    try:
        return delete_existing_node(sid, payload["node_id"])
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/delete_relation")
async def delete_relation_endpoint(payload: Dict[str, Any] = Body(...)):
    sid = payload.get("session_id")
    if not sid: raise HTTPException(status_code=400, detail="session_id is required.")
    try:
        return delete_existing_relation(sid, payload["index"])
    except (IndexError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/delete_attribute")
async def delete_attribute_endpoint(payload: Dict[str, Any] = Body(...)):
    sid = payload.get("session_id")
    if not sid: raise HTTPException(status_code=400, detail="session_id is required.")
    try:
        return delete_existing_attribute(sid, payload["index"])
    except (IndexError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/graph_data")
async def get_graph_data_endpoint(session_id: str):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")
    return build_graph_data(session_id)
