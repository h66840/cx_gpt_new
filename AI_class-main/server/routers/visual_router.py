import json
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from typing import Generator
from server.services.visual_reasoning.ai_client import ai_client

router = APIRouter(tags=["Visual Reasoning"])

async def shortcoming_analysis_generator(image_bytes: bytes, scene_graph_json: str):
    """
    用於生成分析結果的異步生成器
    """
    prompt = f"""
    根据以下图片和对应的Json结果，你分析下有哪些不足。

    JSON结果:
    {scene_graph_json}
    """
    async for chunk in ai_client.analyze_image_stream(image_bytes=image_bytes, prompt=prompt):
        yield chunk


@router.post("/analyze_shortcomings", summary="流式分析场景图的不足")
async def analyze_shortcomings(
    image: UploadFile = File(...),
    scene_graph_json: str = Form(...),
):
    """
    接收图片和场景图JSON，流式返回大模型的分析结果。

    - **image**: 上传的图片文件
    - **scene_graph_json**: 场景图的JSON字符串
    """
    # 在返回 StreamingResponse 之前立即讀取文件內容
    image_bytes = await image.read()
    
    parsed_json = json.loads(scene_graph_json)
    pretty_json = json.dumps(parsed_json, indent=2, ensure_ascii=False)
    
    return StreamingResponse(
        # 將讀取到的 bytes 傳遞給生成器
        shortcoming_analysis_generator(image_bytes, pretty_json),
        media_type="text/plain"
    ) 