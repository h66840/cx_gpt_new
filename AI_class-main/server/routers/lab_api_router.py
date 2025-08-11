import asyncio
import json
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from server.schemas import lab_schemas
from server.services import lab_service

logger = logging.getLogger(__name__)

lab_api_router = APIRouter(
    prefix="",
    tags=["Lab Experiments and Processes"]
)


# --- Lab Process 相关的路由 ---
@lab_api_router.post("/describe-image", summary="Get image caption (stream or non-stream)")
async def api_get_caption(request_data: lab_schemas.ImageCaptionRequest, request: Request):
    accept_header = request.headers.get("accept", "")
    # 检查客户端是否明确要求流式响应 (例如, 通过 'text/event-stream')
    # 或者您可以添加一个查询参数 ?stream=true
    # 这里我们简单判断，如果不是 application/json，就尝试流式
    # 更稳妥的方式是前端请求时明确指定需要流式，例如通过特定的 Content-Type 或 Accept header
    # 或者在 request_data 中添加一个布尔字段 stream: bool = False

    # 假设我们通过一个查询参数来决定是否流式，或者通过 request_data 中的字段
    # 为了简单起见，我们这里直接修改为始终使用流式，如果需要非流式，可以创建另一个端点或添加判断逻辑

    async def stream_generator():
        try:
            async for chunk in lab_service.get_image_caption_stream(
                request_data.image_path,
                request_data.prompt,
            ):
                if chunk.startswith("Error:"):
                    # 对于流中的错误，我们可以选择如何处理
                    # 1. 直接发送错误信息给客户端 (客户端需要能解析)
                    # 2. 记录错误，停止流，后续可能需要更复杂的错误处理机制
                    yield f"data: {json.dumps({'error': chunk})}\n\n"
                    return # 停止流
                yield f"data: {json.dumps({'description_chunk': chunk})}\n\n" 
            yield f"data: {json.dumps({'status': 'done'})}\n\n" # 发送流结束信号
        except Exception as e:
            logger.error(f"Streaming /describe-image 错误: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    # 如果前端明确要求 event-stream，或者我们决定默认流式
    return StreamingResponse(stream_generator(), media_type="text/event-stream")

    # # 非流式的老逻辑 (如果需要保留)
    # try:
    #     result = await lab_service.get_image_caption(
    #         request_data.image_path,
    #         request_data.prompt,
    #     )
    #     if result.get("error"):
    #         raise HTTPException(status_code=400, detail=result["error"])
    #     return result
    # except HTTPException:
    #     raise
    # except Exception as e:
    #     logger.error(f"POST /describe-image 错误: {e}", exc_info=True)
    #     raise HTTPException(status_code=500, detail=str(e))

@lab_api_router.post("/generate-plan", summary="Generate an experimental plan")
async def api_generate_plan(request_data: lab_schemas.PlanGenerationRequest):
    try:
        result = await lab_service.generate_experimental_plan(
            request_data.user_question,
            request_data.image_caption,
            request_data.system_prompt
        )
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST /lab/plan 错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@lab_api_router.post("/execute-plan", summary="Execute a step in the plan (non-streaming)") # Renamed from /execute to avoid conflict
async def api_execute_step(request_data: lab_schemas.PlanRequest):
    try:
        result = await lab_service.execute_plan_step(
            request_data.plan_list,
            request_data.image_caption
        )
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST /lab/execute_step 错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@lab_api_router.post("/execute-plan-stream", summary="Execute a step in the plan (streaming)")
async def api_execute_step_stream(request_data: lab_schemas.PlanRequest):
    async def stream_generator():
        try:
            async for event in lab_service.execute_plan_step_stream(
                request_data.plan_list,
                request_data.image_caption
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)  # 强制刷新流
        except Exception as e:
            logger.error(f"Streaming /execute-plan-stream 错误: {e}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@lab_api_router.post("/decide-answer", summary="Decide the final answer")
async def api_decide_answer(request_data: lab_schemas.AnswerRequest):
    try:
        result = await lab_service.decide_final_answer(
            request_data.reasoning_summary,
            request_data.question,
            request_data.options
        )
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST /lab/decide 错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@lab_api_router.post("/evaluate-response", summary="Grade the experimental response")
async def api_grade_response(request_data: lab_schemas.EvaluateRequest): # Changed from EvaluateRequest to GradeRequest
    try:
        result = await lab_service.grade_experimental_response(
            request_data.predicted,
            request_data.groundtruth,
        )
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST /lab/grade 错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

