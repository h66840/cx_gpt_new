import os
import asyncio
import requests
from typing import List, Optional, AsyncGenerator, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 导入 LangChain 的 OpenAI 聊天模型封装
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 假设 describe_image, describe_image_stream 在你的某个模块中
from lab_process import describe_image, describe_image_stream

load_dotenv()

# --- 全局配置变量 ---
DEFAULT_ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")
DEFAULT_ALIYUN_BASE_URL = os.getenv("ALIYUN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DEFAULT_QWEN_VL_MODEL = "qwen-vl-max"  # 通义千问的视觉理解模型

# --- 工具定义 ---
tools = []

# --- LLM 初始化 (指向阿里云通义千问) ---
llm = ChatOpenAI(
    model=DEFAULT_QWEN_VL_MODEL,  # 使用通义千问模型
    temperature=0.0,  # 可以根据需要调整
    openai_api_key=DEFAULT_ALIYUN_API_KEY,
    openai_api_base=DEFAULT_ALIYUN_BASE_URL
)

# --- LangGraph Agent 配置 ---
memory = MemorySaver()
agent_executor = create_react_agent(llm, tools, checkpointer=memory)

# 会话配置，用于 LangGraph 线程记忆
config = {
    "configurable": {
        "thread_id": "12345"  # 可以是动态生成的 ID
    }
}

# --- 执行计划函数 ---
def execute_plan(plan_list: list[str], image_caption: str) -> str:
    """
    执行多个计划步骤，通过 agent_executor 流处理并汇总中间推理结果。

    :param plan_list: 含多个推理步骤的列表
    :param image_caption: 图像的文字描述，用于提供上下文
    :return: 汇总的推理文本
    """
    if not DEFAULT_ALIYUN_API_KEY:
        return "Error: ALIYUN_API_KEY is not provided. Please set it in .env or environment variables."

    initial_messages = [
        SystemMessage(content=f"图片显示内容如下: {image_caption}"),
        HumanMessage(content="好的，我已经准备好根据图片内容进行推理。")  # 添加一个初始 HumanMessage
    ]

    try:
        agent_executor.invoke({"messages": initial_messages}, config=config)
    except Exception as e:
        print(f"Agent 初始化失败: {e}")
        return f"Error: Agent initialization failed. {e}"

    reasoning_summaries = []

    for plan in plan_list:
        step_output = ""
        prompt = (
            f"现在根据图片和问题上下文执行以下推理步骤:\n{plan}"
            f"请保持回复简洁，不超过5句话或200字。请用中文回复。"
        )

        try:
            for chunk in agent_executor.stream(
                    {"messages": [HumanMessage(content=prompt)]},  # 后续步骤仍然只发 HumanMessage
                    stream_mode="values",
                    config=config,
            ):
                message = chunk["messages"][-1]
                if isinstance(message, AIMessage):
                    step_output += message.content.strip() + "\n"

            reasoning_summaries.append({
                "step": plan,
                "output": step_output.strip()
            })
        except Exception as e:
            print(f"执行步骤 '{plan}' 时出错: {e}")
            reasoning_summaries.append({
                "step": plan,
                "output": f"Error executing step: {e}"
            })

    return "\n\n".join(
        f"步骤: {r['step']}\n输出: {r['output']}" for r in reasoning_summaries
    )

async def execute_plan_stream(plan_list: list[str], image_caption: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    执行多个计划步骤，通过 agent_executor 流处理并逐步返回中间推理结果。

    :param plan_list: 含多个推理步骤的列表
    :param image_caption: 图像的文字描述，用于提供上下文
    :yield: 流式返回每个步骤的推理过程和结果
    """
    yield {"event": "init", "data": {"total_steps": len(plan_list)}}

    if not DEFAULT_ALIYUN_API_KEY:
        yield {"event": "error", "data": "Error: ALIYUN_API_KEY is not provided."}
        return

    initial_messages = [
        SystemMessage(content=f"图片显示内容如下: {image_caption}"),
        HumanMessage(content="好的，我已经准备好根据图片内容进行推理。")  # 添加一个初始 HumanMessage
    ]

    try:
        agent_executor.invoke({"messages": initial_messages}, config=config)
    except Exception as e:
        yield {"event": "error", "data": f"Agent initialization failed: {e}"}
        return

    for i, plan in enumerate(plan_list):
        yield {"event": "step_start", "data": {"step_index": i, "step": plan}}

        prompt = (
            f"现在根据图片和问题上下文执行以下推理步骤:\n{plan}"
            f"请保持回复简洁，不超过5句话或200字。请用中文回复。"
        )

        step_output_content = ""

        try:
            def sync_stream():
                return agent_executor.stream(
                    {"messages": [HumanMessage(content=prompt)]},
                    stream_mode="values",
                    config=config,
                )

            for chunk in await asyncio.to_thread(sync_stream):
                message = chunk["messages"][-1]
                if isinstance(message, AIMessage) and message.content:
                    chunk_content = message.content.strip()
                    step_output_content += chunk_content
                    yield {"event": "chunk", "data": {
                        "step_index": i,
                        "content": chunk_content
                    }}
                    await asyncio.sleep(0.01)  # 微小延迟确保异步刷新

            yield {"event": "step_complete", "data": {
                "step_index": i,
                "final_output": step_output_content
            }}
        except Exception as e:
            yield {"event": "error", "data": f"Error executing step {i}: {plan}. Details: {e}"}
            continue

    yield {"event": "complete", "data": {}}

async def async_main():
    # 示例数据准备
    plan_list = [
        "识别图片中艺术家签名的位置。",
        "阅读签名以确定艺术家的名字。",
        "通过与作品标题“Jane Avril”和已知创作者进行交叉引用来验证名字。"
    ]

    image_url_for_description = "https://modelscope.cn/datasets/modelscope/MMMU-Reasoning-Distill-Validation/resolve/master/images/validation_Art_3_1.png"
    print(f"正在获取图片描述 (URL: {image_url_for_description})...")

    image_caption = describe_image(image_url_for_description, prompt="请用中文详细描述图片内容。")

    if "Error:" in image_caption:
        print(f"获取图片描述失败: {image_caption}")
        return
    else:
        print(f"图片描述: {image_caption[:150]}...")

    print("\n=== 开始流式处理 LangGraph Agent ===")
    async for event in execute_plan_stream(plan_list, image_caption):
        event_type = event["event"]
        data = event["data"]

        if event_type == "init":
            print(f"初始化完成，总步骤数: {data['total_steps']}", flush=True)
        elif event_type == "step_start":
            print(f"\n▶ 开始步骤 {data['step_index'] + 1}: {data['step']}", flush=True)
        elif event_type == "chunk":
            print(f"    | {data['content']}", end="", flush=True)
        elif event_type == "step_complete":
            print(f"\n✓ 步骤 {data['step_index'] + 1} 完成。最终输出：{data.get('final_output', 'N/A')[:50]}...", flush=True)
        elif event_type == "error":
            print(f"\n❌ 错误发生: {data}", flush=True)
        elif event_type == "complete":
            print(f"\n=== 所有步骤执行完毕 ===", flush=True)

if __name__ == "__main__":
    asyncio.run(async_main())