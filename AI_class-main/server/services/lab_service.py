
import logging

from typing import Dict, Any, Set, List, Optional, AsyncGenerator

# 用于独立会话

# 假设 lab_process 中的函数按原样导入和使用
from lab_process.caption import describe_image, describe_image_stream
from lab_process.planner import generate_plan
from lab_process.executor import execute_plan, execute_plan_stream
from lab_process.decider import decide_answer
from lab_process.grade import evaluate_response

logger = logging.getLogger(__name__)




# 图像描述服务逻辑
async def get_image_caption(image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
    logger.info(f"Lab Service: 请求图像描述 for {image_path}")
    try:
        description = describe_image(image_path, prompt)  # 假设 describe_image 是同步的，返回字符串
        return {"description": description, "error": None}  # 返回字典，兼容路由
    except Exception as e:
        logger.error(f"获取图像描述失败: {e}")
        return {"description": None, "error": str(e)}

# 新增：图像描述流式服务逻辑
async def get_image_caption_stream(image_path: str, prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
    logger.info(f"Lab Service: 请求图像描述 (流式) for {image_path}")
    try:
        async for chunk in describe_image_stream(image_path, prompt):
            yield chunk
    except Exception as e:
        logger.error(f"获取图像描述流失败: {e}")
        yield f"Error: {str(e)}" # 在流中传递错误信息

# 生成计划服务逻辑
async def generate_experimental_plan(user_question: str, image_caption: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
    logger.info(f"Lab Service: 请求生成计划 for '{user_question}'")
    try:
        plan = generate_plan(user_question, image_caption, system_prompt)  # 假设返回 List[str]
        return {"plan": plan, "error": None}
    except Exception as e:
        logger.error(f"生成计划失败: {e}")
        return {"plan": None, "error": str(e)}

# 执行计划步骤服务逻辑
async def execute_plan_step(step_description: List[str], image_caption: str) -> Dict[str, Any]:
    logger.info(f"Lab Service: 请求执行计划步骤 '{step_description}'")
    try:
        result = execute_plan(step_description, image_caption)  # 假设返回字符串或字典
        return {"result": result, "error": None}
    except Exception as e:
        logger.error(f"执行计划步骤失败: {e}")
        return {"result": None, "error": str(e)}

# 新增：执行计划步骤流式服务逻辑
async def execute_plan_step_stream(plan_list: List[str], image_caption: str) -> AsyncGenerator[Dict[str, Any], None]:
    logger.info(f"Lab Service: 请求执行计划步骤 (流式) for {len(plan_list)} steps")
    try:
        async for event_data in execute_plan_stream(plan_list, image_caption):
            yield event_data
    except Exception as e:
        logger.error(f"执行计划步骤流失败: {e}")
        yield {"event": "error", "data": f"Error during streaming plan execution: {str(e)}"} # 在流中传递错误信息

# 决策答案服务逻辑
async def decide_final_answer(reasoning_summary: str, question: str, options: List[str]) -> Dict[str, Any]:
    logger.info(f"Lab Service: 请求决策答案 for '{question}'")
    try:
        result = decide_answer(reasoning_summary, question, options)  # 假设返回对象
        final_answer = result.content if hasattr(result, 'content') else result
        return {"result": final_answer, "error": None}
    except Exception as e:
        logger.error(f"决策答案失败: {e}")
        return {"result": None, "error": str(e)}

# 评分服务逻辑
async def grade_experimental_response(predicted: str, groundtruth: str) -> Dict[str, Any]:
    logger.info(f"Lab Service: 请求评分 for predicted: {predicted[:50]}...")
    try:
        response = evaluate_response(predicted, groundtruth)  # 假设返回字典
        return response  # 直接返回，与重构前一致
    except Exception as e:
        logger.error(f"评分失败: {e}")
        return {"error": f"评分失败: {e}"}

