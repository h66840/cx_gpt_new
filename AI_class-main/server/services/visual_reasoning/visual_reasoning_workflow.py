import json
import asyncio
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import os

from server.services.visual_reasoning.semantic_similarity import should_add_relationship
from server.services.visual_reasoning.scene_graph_api import (
    get_current_scene_graph_state,
    query_node_with_hidden_attributes,
    add_entity_function,
    add_relationship_function,
)

try:
    from langgraph.graph import StateGraph, START, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    print("LangGraph not installed. Using fallback simple workflow.")
    LANGGRAPH_AVAILABLE = False

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"

@dataclass
class SubQuestion:
    id: str
    content: str
    status: TaskStatus = TaskStatus.PENDING
    visual_analysis_result: Optional[Dict] = None
    discovered_entities: List[Dict] = field(default_factory=list)

class WorkflowState(TypedDict):
    session_id: str
    original_question: str
    subquestions: List[SubQuestion]
    current_subquestion_index: int
    scene_graph_nodes: List[str]
    final_answer: Optional[str]
    image_data: Optional[bytes]

class VisualReasoningWorkflow:
    def __init__(self, sse_manager=None):
        self.sse_manager = sse_manager
        self.workflow = self._build_workflow() if LANGGRAPH_AVAILABLE else None

    def _build_workflow(self):
        workflow = StateGraph(WorkflowState)
        workflow.add_node("process_subquestion", self._process_subquestion)
        workflow.add_node("finalize_answer", self._finalize_answer)
        workflow.add_conditional_edges(
            START,
            lambda state: "finalize_answer" if state["current_subquestion_index"] >= len(state["subquestions"]) else "process_subquestion",
        )
        workflow.add_conditional_edges(
            "process_subquestion",
            lambda state: "finalize_answer" if state["current_subquestion_index"] >= len(state["subquestions"]) else "process_subquestion",
        )
        workflow.add_edge("finalize_answer", END)
        return workflow.compile()

    async def _process_subquestion(self, state: WorkflowState) -> WorkflowState:
        index = state["current_subquestion_index"]
        subquestion = state["subquestions"][index]
        subquestion.status = TaskStatus.RUNNING
        
        # Simulate visual analysis and entity alignment
        # In a real scenario, this would involve complex logic and API calls
        
        subquestion.visual_analysis_result = {"key_finding": f"Analysis of '{subquestion.content}'"}
        subquestion.status = TaskStatus.COMPLETED
        
        state["current_subquestion_index"] += 1
        return state

    async def _finalize_answer(self, state: WorkflowState) -> WorkflowState:
        # Simple final answer synthesis
        findings = [sq.visual_analysis_result['key_finding'] for sq in state['subquestions'] if sq.visual_analysis_result]
        state["final_answer"] = " ".join(findings)
        return state

    async def run(self, initial_state: dict):
        if not self.workflow:
            # Fallback to a simple loop if LangGraph is not available
            state = initial_state
            while state["current_subquestion_index"] < len(state["subquestions"]):
                state = await self._process_subquestion(state)
            state = await self._finalize_answer(state)
            return state

        config = {"configurable": {"thread_id": initial_state["session_id"]}}
        async for event in self.workflow.astream(initial_state, config):
            # Stream events if needed
            pass
        return await self.workflow.ainvoke(initial_state, config)

class WorkflowController:
    def __init__(self, sse_manager=None):
        self.sse_manager = sse_manager
        self.workflows: Dict[str, VisualReasoningWorkflow] = {}

    async def start_workflow(self, session_id: str, initial_state: Dict[str, Any]):
        workflow = VisualReasoningWorkflow(self.sse_manager)
        self.workflows[session_id] = workflow
        
        subquestions = [SubQuestion(id=f"sq-{i}", content=sq) for i, sq in enumerate(initial_state["subquestions"])]
        
        state: WorkflowState = {
            "session_id": session_id,
            "original_question": initial_state["original_question"],
            "subquestions": subquestions,
            "current_subquestion_index": 0,
            "scene_graph_nodes": initial_state["scene_graph_nodes"],
            "final_answer": None,
            "image_data": initial_state.get("image_data"),
        }
        
        final_state = await workflow.run(state)
        return final_state

workflow_controller = WorkflowController()
