import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


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
    status: TaskStatus
    visual_analysis_result: Optional[str] = None
    discovered_entities: List[Dict[str, Any]] = None
    reasoning: Optional[str] = None


class SimpleWorkflowController:
    """简化的工作流控制器，不依赖LangGraph"""

    def __init__(self):
        self.active_workflows = {}

    async def start_workflow(self, session_id: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """启动新的工作流"""
        print(f"🚀 启动简化工作流: {session_id}")
        
        try:
            original_question = initial_state["original_question"]
            subquestions = initial_state["subquestions"]
            reasoning_evidence = initial_state.get("reasoning_evidence", [])
            
            # 创建工作流状态
            workflow_state = {
                "session_id": session_id,
                "original_question": original_question,
                "subquestions": [
                    {
                        "id": f"subq_{i}",
                        "content": subq,
                        "status": TaskStatus.PENDING.value,
                        "result": None
                    }
                    for i, subq in enumerate(subquestions)
                ],
                "reasoning_evidence": reasoning_evidence,
                "current_index": 0,
                "status": "started",
                "discovered_entities": [],
                "final_answer": None
            }
            
            # 存储工作流状态
            self.active_workflows[session_id] = workflow_state
            
            print(f"✅ 工作流 {session_id} 已启动，包含 {len(subquestions)} 个子问题")
            
            return {
                "status": "workflow_started",
                "session_id": session_id,
                "workflow_state": workflow_state
            }
            
        except Exception as e:
            print(f"❌ 启动工作流失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def pause_workflow(self, session_id: str) -> Dict[str, Any]:
        """暂停工作流"""
        if session_id in self.active_workflows:
            self.active_workflows[session_id]["status"] = "paused"
            print(f"⏸️ 工作流 {session_id} 已暂停")
            return {"status": "paused", "session_id": session_id}
        return {"error": "Workflow not found"}

    async def resume_workflow(self, session_id: str) -> Dict[str, Any]:
        """恢复工作流"""
        if session_id in self.active_workflows:
            self.active_workflows[session_id]["status"] = "running"
            print(f"▶️ 工作流 {session_id} 已恢复")
            return {"status": "resumed", "session_id": session_id}
        return {"error": "Workflow not found"}

    async def modify_subquestion(self, session_id: str, subquestion_id: str, new_content: str) -> Dict[str, Any]:
        """修改子问题"""
        if session_id in self.active_workflows:
            workflow = self.active_workflows[session_id]
            
            # 查找并修改子问题
            for subq in workflow["subquestions"]:
                if subq["id"] == subquestion_id:
                    subq["content"] = new_content
                    print(f"✏️ 子问题 {subquestion_id} 已修改: {new_content}")
                    return {"status": "modified", "subquestion_id": subquestion_id}
            
            return {"error": "Subquestion not found"}
        
        return {"error": "Workflow not found"}

    async def add_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """添加用户输入"""
        if session_id in self.active_workflows:
            workflow = self.active_workflows[session_id]
            
            # 添加用户输入到工作流状态
            if "user_inputs" not in workflow:
                workflow["user_inputs"] = []
            
            workflow["user_inputs"].append({
                "timestamp": asyncio.get_event_loop().time(),
                "input": user_input
            })
            
            print(f"💬 用户输入已添加到工作流 {session_id}: {user_input}")
            return {"status": "input_added", "user_input": user_input}
        
        return {"error": "Workflow not found"}

    async def execute_subquestion(self, session_id: str, subquestion_index: int) -> Dict[str, Any]:
        """执行单个子问题"""
        if session_id not in self.active_workflows:
            return {"error": "Workflow not found"}
        
        workflow = self.active_workflows[session_id]
        subquestions = workflow["subquestions"]
        
        if subquestion_index >= len(subquestions):
            return {"error": "Subquestion index out of range"}
        
        subquestion = subquestions[subquestion_index]
        
        # 防重复执行检查
        if subquestion["status"] == TaskStatus.RUNNING.value:
            print(f"⚠️ 子问题 {subquestion_index + 1} 正在执行中，跳过重复请求")
            return {
                "status": "already_running",
                "subquestion_index": subquestion_index,
                "message": "Subquestion is already running"
            }
        
        if subquestion["status"] == TaskStatus.COMPLETED.value:
            print(f"⚠️ 子问题 {subquestion_index + 1} 已经完成，跳过重复请求")
            return {
                "status": "already_completed",
                "subquestion_index": subquestion_index,
                "result": subquestion.get("result"),
                "message": "Subquestion is already completed"
            }
        
        try:
            print(f"🔍 执行子问题 {subquestion_index + 1}: {subquestion['content']}")
            
            # 设置状态为运行中
            subquestion["status"] = TaskStatus.RUNNING.value
            
            # 模拟视觉推理分析
            result = await self._simulate_visual_analysis(subquestion["content"])
            
            # 更新结果
            subquestion["result"] = result
            subquestion["status"] = TaskStatus.COMPLETED.value
            
            # 更新当前索引
            workflow["current_index"] = subquestion_index + 1
            
            # 检查是否所有子问题都完成了
            if workflow["current_index"] >= len(subquestions):
                workflow["status"] = "completed"
                await self._generate_final_answer(session_id)
            
            print(f"✅ 子问题 {subquestion_index + 1} 执行完成")
            
            return {
                "status": "subquestion_completed",
                "subquestion_index": subquestion_index,
                "result": result
            }
            
        except Exception as e:
            subquestion["status"] = TaskStatus.FAILED.value
            subquestion["error"] = str(e)
            print(f"❌ 子问题 {subquestion_index + 1} 执行失败: {str(e)}")
            
            return {
                "status": "subquestion_failed",
                "subquestion_index": subquestion_index,
                "error": str(e)
            }

    async def _simulate_visual_analysis(self, subquestion: str) -> Dict[str, Any]:
        """模拟视觉分析（稍后可替换为真实的API调用）"""
        # 添加延迟以模拟分析过程
        await asyncio.sleep(1)
        
        # 返回模拟结果
        return {
            "visual_descriptions": [
                f"在图像中观察到与'{subquestion}'相关的视觉特征",
                f"识别出与问题相关的关键元素"
            ],
            "discovered_entities": [
                {
                    "entity_name": f"分析实体_{len(subquestion)}",
                    "entity_type": "VisualElement",
                    "confidence": 0.8,
                    "description": f"通过分析'{subquestion}'发现的实体"
                }
            ],
            "reasoning": f"基于视觉分析，我们可以推断出关于'{subquestion}'的以下信息...",
            "confidence": 0.85
        }

    async def _generate_final_answer(self, session_id: str) -> None:
        """生成最终答案"""
        workflow = self.active_workflows[session_id]
        
        try:
            # 汇总所有子问题的结果
            completed_results = [
                subq["result"] for subq in workflow["subquestions"]
                if subq["status"] == TaskStatus.COMPLETED.value and subq.get("result")
            ]
            
            if not completed_results:
                workflow["final_answer"] = "无法生成答案：没有成功完成的子问题分析"
                return
            
            # 生成综合答案
            descriptions = []
            entities = []
            
            for result in completed_results:
                if "visual_descriptions" in result:
                    descriptions.extend(result["visual_descriptions"])
                if "discovered_entities" in result:
                    entities.extend([e["entity_name"] for e in result["discovered_entities"]])
            
            final_answer = (
                f"基于对问题 '{workflow['original_question']}' 的综合分析：\n\n"
                f"视觉观察：\n" + "\n".join([f"• {desc}" for desc in descriptions[:3]]) + "\n\n"
                f"发现的关键元素：{', '.join(entities[:5]) if entities else '无'}\n\n"
                f"结论：通过多轮视觉推理分析，我们获得了关于原始问题的详细信息。"
            )
            
            workflow["final_answer"] = final_answer
            print(f"🎯 工作流 {session_id} 的最终答案已生成")
            
        except Exception as e:
            workflow["final_answer"] = f"生成最终答案时发生错误: {str(e)}"
            print(f"❌ 生成最终答案失败: {str(e)}")

    def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """获取工作流状态"""
        if session_id in self.active_workflows:
            return self.active_workflows[session_id]
        return {"error": "Workflow not found"}

    def clear_workflow(self, session_id: str) -> Dict[str, Any]:
        """清理工作流状态"""
        if session_id in self.active_workflows:
            del self.active_workflows[session_id]
            print(f"🧹 工作流 {session_id} 已清理")
            return {"status": "cleared", "session_id": session_id}
        return {"error": "Workflow not found"}


# 全局简化工作流控制器实例
simple_workflow_controller = SimpleWorkflowController()

# 导出
__all__ = ['SimpleWorkflowController', 'simple_workflow_controller']
