from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form
from typing import Dict, Any, List
import traceback

# Import new state management functions
from server.services.visual_reasoning.state import (
    get_graph,
    get_hidden_attributes,
    get_current_image,
)
from server.services.visual_reasoning.Q_Process import QuestionProcessor
from server.services.visual_reasoning.visual_reasoning_workflow import workflow_controller
from server.services.visual_reasoning.caption import miscellaneous_analysis


router = APIRouter()

@router.post("/process_question")
async def process_question_api(payload: Dict[str, Any] = Body(...)):
    question = payload.get("question")
    session_id = payload.get("session_id")

    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")

    try:
        # Fetch session-specific data from Redis
        graph = get_graph(session_id)
        hidden_attributes = get_hidden_attributes(session_id)
        scene_graph_nodes = list(graph.nodes())
        
        processor = QuestionProcessor(graph=graph, hidden_attributes=hidden_attributes)
        result = processor.extract_entities_and_subquestions(question, scene_graph_nodes)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

@router.post("/start_visual_workflow")
async def start_visual_workflow(payload: Dict[str, Any] = Body(...)):
    if not workflow_controller:
        raise HTTPException(status_code=500, detail="Visual reasoning workflow not available")
    
    try:
        session_id = payload.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required.")

        original_question = payload.get("original_question", "")
        subquestions = payload.get("subquestions", [])
        
        if not original_question or not subquestions:
            raise HTTPException(status_code=400, detail="Original question and subquestions are required")
        
        # Fetch graph and image data from Redis using session_id
        graph = get_graph(session_id)
        image_data = get_current_image(session_id)
        scene_graph_nodes = list(graph.nodes())
        
        initial_state = {
            "session_id": session_id,
            "original_question": original_question,
            "subquestions": subquestions,
            "scene_graph_nodes": scene_graph_nodes,
            "reasoning_evidence": payload.get("reasoning_evidence", []),
            "image_data": image_data,
        }
        
        result = await workflow_controller.start_workflow(session_id, initial_state)
        
        return {
            "status": "workflow_started",
            "session_id": session_id,
            "workflow_result": result
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

# Other endpoints like pause, resume, clear also need session_id
@router.post("/pause_workflow")
async def pause_workflow(payload: Dict[str, str] = Body(...)):
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required.")
    if not workflow_controller:
        raise HTTPException(status_code=500, detail="Workflow controller not available.")
    return await workflow_controller.pause_workflow(session_id)

@router.post("/resume_workflow")
async def resume_workflow(payload: Dict[str, str] = Body(...)):
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required.")
    if not workflow_controller:
        raise HTTPException(status_code=500, detail="Workflow controller not available.")
    return await workflow_controller.resume_workflow(session_id)

@router.post("/clear_workflow")
async def clear_workflow(payload: Dict[str, str] = Body(...)):
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required.")
    if not workflow_controller:
        raise HTTPException(status_code=500, detail="Workflow controller not available.")
    return workflow_controller.clear_workflow(session_id)

@router.post("/generate_scene_graph")
async def generate_scene_graph(image: UploadFile = File(...), prompt: str = Form(...)):
    try:
        image_content = await image.read()
        result = await miscellaneous_analysis(image_content, prompt)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
