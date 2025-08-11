import os
import json
import asyncio
import traceback
import uuid
import time
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk, HumanMessage
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src import executor, config, retriever
from src.core import HistoryManager
from src.agents import agent_manager
from src.models import select_model
from src.utils.logging_config import logger
from src.agents.tools_factory import get_all_tools
from server.routers.auth_router import get_admin_user
from server.utils.auth_middleware import get_required_user, get_db
from server.models.user_model import User
from server.models.thread_model import Thread

chat = APIRouter(prefix="/chat")


@chat.get("/default_agent")
async def get_default_agent(current_user: User = Depends(get_required_user)):
    """
    获取系统默认的智能体ID

    参数:
        current_user: 通过身份验证的当前用户对象

    返回:
        dict: 包含默认智能体ID的字典

    异常:
        若获取失败则返回500错误
    """
    try:
        default_agent_id = config.default_agent_id
        # 如果没有设置默认智能体，尝试获取第一个可用的智能体
        if not default_agent_id:
            agents = await agent_manager.get_agents_info()
            if agents:
                default_agent_id = agents[0].get("name", "")

        return {"default_agent_id": default_agent_id}
    except Exception as e:
        logger.error(f"获取默认智能体出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取默认智能体出错: {str(e)}")


@chat.post("/set_default_agent")
async def set_default_agent(agent_id: str = Body(..., embed=True), current_user=Depends(get_admin_user)):
    """
    设置系统默认智能体ID（管理员权限）

    参数:
        agent_id: 要设置为默认的智能体ID
        current_user: 管理员用户对象

    返回:
        dict: 操作结果和设置的智能体ID

    异常:
        若智能体不存在返回404，其他错误返回500
    """
    try:
        # 验证智能体是否存在
        agents = await agent_manager.get_agents_info()
        agent_ids = [agent.get("name", "") for agent in agents]

        if agent_id not in agent_ids:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 不存在")

        # 设置默认智能体ID
        config.default_agent_id = agent_id
        # 保存配置
        config.save()
        print(f"设置默认智能体为: {agent_id}")  # 新加调试

        return {"success": True, "default_agent_id": agent_id}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"设置默认智能体出错: {e}")
        raise HTTPException(status_code=500, detail=f"设置默认智能体出错: {str(e)}")


@chat.get("/")
async def chat_get(current_user: User = Depends(get_required_user)):
    """聊天服务的健康检查端点（需登录验证）"""
    return "Chat Get!"


@chat.post("/")
async def chat_post(
        query: str = Body(...),
        meta: dict = Body(None),
        history: list[dict] | None = Body(None),
        thread_id: str | None = Body(None),
        current_user: User = Depends(get_required_user)):
    """
    处理用户聊天请求的主端点

    参数:
        query: 用户输入的查询文本
        meta: 包含聊天元数据的字典（如系统提示、模型配置等）
        history: 历史对话记录列表
        thread_id: 对话线程ID
        current_user: 当前认证用户

    返回:
        StreamingResponse: 流式响应对象，包含聊天响应

    处理流程:
        1. 初始化历史管理器和模型
        2. 根据元数据决定是否进行知识库检索
        3. 流式生成模型响应
        4. 处理响应过程中的异常
    """
    model = select_model()
    meta["server_model_name"] = model.model_name
    history_manager = HistoryManager(history, system_prompt=meta.get("system_prompt"))
    logger.debug(f"Received query: {query} with meta: {meta}")

    def make_chunk(content=None, **kwargs):
        """构造流式响应的数据块"""
        return json.dumps({
            "response": content,
            "meta": meta,
            **kwargs
        }, ensure_ascii=False).encode('utf-8') + b"\n"

    def need_retrieve(meta):
        """判断是否需要执行知识库检索"""
        return meta.get("use_web") or meta.get("use_graph") or meta.get("db_id")

    def generate_response():
        """生成流式响应的核心逻辑"""
        modified_query = query
        refs = None

        # 处理知识库检索
        if meta and need_retrieve(meta):
            chunk = make_chunk(status="searching")
            yield chunk

            try:
                modified_query, refs = retriever(modified_query, history_manager.messages, meta)
            except Exception as e:
                logger.error(f"Retriever error: {e}, {traceback.format_exc()}")
                yield make_chunk(message=f"Retriever error: {e}", status="error")
                return

            yield make_chunk(status="generating")

        messages = history_manager.get_history_with_msg(modified_query, max_rounds=meta.get('history_round'))
        history_manager.add_user(query)  # 注意这里使用原始查询

        content = ""
        reasoning_content = ""
        try:
            # 流式处理模型响应
            for delta in model.predict(messages, stream=True):
                # 处理推理内容（如文心一言的特殊结构）
                if not delta.content and hasattr(delta, 'reasoning_content'):
                    reasoning_content += delta.reasoning_content or ""
                    chunk = make_chunk(reasoning_content=reasoning_content, status="reasoning")
                    yield chunk
                    continue

                # 处理完整响应（如文心一言的特殊结构）
                if hasattr(delta, 'is_full') and delta.is_full:
                    content = delta.content
                else:
                    content += delta.content or ""

                chunk = make_chunk(content=delta.content, status="loading")
                yield chunk

            logger.debug(f"Final response: {content}")
            logger.debug(f"Final reasoning response: {reasoning_content}")
            yield make_chunk(status="finished",
                             history=history_manager.update_ai(content),
                             refs=refs)
        except Exception as e:
            logger.error(f"Model error: {e}, {traceback.format_exc()}")
            yield make_chunk(message=f"Model error: {e}", status="error")
            return

    return StreamingResponse(generate_response(), media_type='application/json')


@chat.post("/call")
async def call(query: str = Body(...), meta: dict = Body(None), current_user: User = Depends(get_required_user)):
    """
    直接调用模型进行简单问答

    参数:
        query: 用户查询文本
        meta: 模型配置元数据
        current_user: 当前认证用户

    返回:
        dict: 包含模型响应的字典
    """
    meta = meta or {}
    model = select_model(model_provider=meta.get("model_provider"), model_name=meta.get("model_name"))

    async def predict_async(query):
        """异步执行模型预测"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, model.predict, query)

    response = await predict_async(query)
    logger.debug({"query": query, "response": response.content})

    return {"response": response.content}


@chat.get("/agent")
async def get_agent(current_user: User = Depends(get_required_user)):
    """
    获取所有可用智能体列表

    参数:
        current_user: 当前认证用户

    返回:
        dict: 包含智能体列表的字典
    """
    agents = await agent_manager.get_agents_info()
    logger.debug(f"agents: {agents}")
    return {"agents": agents}


@chat.post("/agent/{agent_name}")
async def chat_agent(agent_name: str,
                     query: str = Body(...),
                     config: dict = Body({}),
                     meta: dict = Body({}),
                     current_user: User = Depends(get_required_user)):
    """
    使用指定智能体进行对话

    参数:
        agent_name: 目标智能体名称
        query: 用户查询文本
        config: 智能体运行时配置
        meta: 请求元数据
        current_user: 当前认证用户

    返回:
        StreamingResponse: 智能体生成的流式响应

    处理流程:
        1. 初始化请求元数据
        2. 获取智能体实例
        3. 生成或使用现有线程ID
        4. 流式处理智能体响应
    """
    meta.update({
        "query": query,
        "agent_name": agent_name,
        "server_model_name": config.get("model", agent_name),
        "thread_id": config.get("thread_id"),
        "user_id": current_user.id
    })

    # 将meta和thread_id整合到config中
    def make_chunk(content=None, **kwargs):
        """构造智能体流式响应的数据块"""
        return json.dumps({
            "request_id": meta.get("request_id"),
            "response": content,
            **kwargs
        }, ensure_ascii=False).encode('utf-8') + b"\n"

    async def stream_messages():
        """智能体消息流处理核心逻辑"""
        # 代表服务端已经收到了请求
        yield make_chunk(status="init", meta=meta, msg=HumanMessage(content=query).model_dump())

        try:
            agent = agent_manager.get_agent(agent_name)
        except Exception as e:
            logger.error(f"Error getting agent {agent_name}: {e}, {traceback.format_exc()}")
            yield make_chunk(message=f"Error getting agent {agent_name}: {e}", status="error")
            return

        messages = [{"role": "user", "content": query}]

        # 构造运行时配置，如果没有thread_id则生成一个
        config["user_id"] = current_user.id
        if "thread_id" not in config or not config["thread_id"]:
            config["thread_id"] = str(uuid.uuid4())
            logger.debug(f"没有thread_id，生成一个: {config['thread_id']=}")

        runnable_config = {"configurable": {**config}}

        try:
            # 流式处理智能体响应
            async for msg, metadata in agent.stream_messages(messages, config_schema=runnable_config):
                # logger.debug(f"msg: {msg.model_dump()}, metadata: {metadata}")
                if isinstance(msg, AIMessageChunk):
                    yield make_chunk(content=msg.content,
                                     msg=msg.model_dump(),
                                     metadata=metadata,
                                     status="loading")
                else:
                    yield make_chunk(msg=msg.model_dump(),
                                     metadata=metadata,
                                     status="loading")

            yield make_chunk(status="finished", meta=meta)
        except Exception as e:
            logger.error(f"Error streaming messages: {e}, {traceback.format_exc()}")
            yield make_chunk(message=f"Error streaming messages: {e}", status="error")

    return StreamingResponse(stream_messages(), media_type='application/json')


@chat.get("/models")
async def get_chat_models(model_provider: str, current_user: User = Depends(get_admin_user)):
    """
    获取指定模型提供商的可用模型列表（管理员权限）

    参数:
        model_provider: 模型提供商名称
        current_user: 管理员用户

    返回:
        dict: 包含模型列表的字典
    """
    model = select_model(model_provider=model_provider)
    return {"models": model.get_models()}


@chat.post("/models/update")
async def update_chat_models(model_provider: str, model_names: list[str], current_user=Depends(get_admin_user)):
    """
    更新指定模型提供商的模型列表（管理员权限）

    参数:
        model_provider: 模型提供商名称
        model_names: 新的模型名称列表
        current_user: 管理员用户

    返回:
        dict: 更新后的模型列表
    """
    config.model_names[model_provider]["models"] = model_names
    config._save_models_to_file()
    return {"models": config.model_names[model_provider]["models"]}


@chat.get("/tools")
async def get_tools(current_user: User = Depends(get_admin_user)):
    """
    获取所有可用工具列表（管理员权限）

    参数:
        current_user: 管理员用户

    返回:
        dict: 包含工具名称列表的字典
    """
    return {"tools": list(get_all_tools().keys())}


@chat.post("/agent/{agent_name}/config")
async def save_agent_config(
        agent_name: str,
        config: dict = Body(...),
        current_user: User = Depends(get_admin_user)
):
    """
    保存智能体配置到YAML文件（管理员权限）

    参数:
        agent_name: 智能体名称
        config: 要保存的配置字典
        current_user: 管理员用户

    返回:
        dict: 操作结果消息

    异常:
        若智能体不存在返回404，保存失败返回500
    """
    try:
        # 获取Agent实例和配置类
        agent = agent_manager.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_name} 不存在")

        # 使用配置类的save_to_file方法保存配置
        config_cls = agent.config_schema
        result = config_cls.save_to_file(config, agent_name)

        if result:
            return {"success": True, "message": f"智能体 {agent_name} 配置已保存"}
        else:
            raise HTTPException(status_code=500, detail="保存智能体配置失败")

    except Exception as e:
        logger.error(f"保存智能体配置出错: {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"保存智能体配置出错: {str(e)}")


@chat.get("/agent/{agent_name}/history")
async def get_agent_history(
        agent_name: str,
        thread_id: str,
        current_user: User = Depends(get_required_user)
):
    """
    获取指定智能体的历史消息

    参数:
        agent_name: 智能体名称
        thread_id: 对话线程ID
        current_user: 当前认证用户

    返回:
        dict: 包含历史消息的字典

    异常:
        若智能体不存在返回404，其他错误返回500
    """
    try:
        # 获取Agent实例和配置类
        agent = agent_manager.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_name} 不存在")

        # 获取历史消息
        history = await agent.get_history(user_id=current_user.id, thread_id=thread_id)
        return {"history": history}

    except Exception as e:
        logger.error(f"获取智能体历史消息出错: {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取智能体历史消息出错: {str(e)}")


@chat.get("/agent/{agent_name}/config")
async def get_agent_config(
        agent_name: str,
        current_user: User = Depends(get_required_user)
):
    """
    从YAML文件加载智能体配置

    参数:
        agent_name: 智能体名称
        current_user: 当前认证用户

    返回:
        dict: 包含智能体配置的字典

    异常:
        若智能体不存在返回404，其他错误返回500
    """
    try:
        # 检查智能体是否存在
        if not (agent := agent_manager.get_agent(agent_name)):
            raise HTTPException(status_code=404, detail=f"智能体 {agent_name} 不存在")

        config = agent.config_schema.from_runnable_config(config={}, agent_name=agent_name)
        return {"success": True, "config": config}

    except Exception as e:
        logger.error(f"加载智能体配置出错: {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"加载智能体配置出错: {str(e)}")


# ==================== 线程管理 API ====================

class ThreadCreate(BaseModel):
    """创建线程的请求模型"""
    title: str | None = None
    agent_id: str
    description: str | None = None
    metadata: dict | None = None


class ThreadResponse(BaseModel):
    """线程响应模型"""
    id: str
    user_id: str
    agent_id: str
    title: str | None = None
    description: str | None = None
    create_at: str
    update_at: str


@chat.post("/thread", response_model=ThreadResponse)
async def create_thread(
        thread: ThreadCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_required_user)
):
    """
    创建新的对话线程

    参数:
        thread: 线程创建请求体
        db: 数据库会话
        current_user: 当前认证用户

    返回:
        ThreadResponse: 创建成功的线程信息
    """
    thread_id = str(uuid.uuid4())

    new_thread = Thread(
        id=thread_id,
        user_id=current_user.id,
        agent_id=thread.agent_id,
        title=thread.title or "新对话",
        description=thread.description,
    )

    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)

    return {
        "id": new_thread.id,
        "user_id": new_thread.user_id,
        "agent_id": new_thread.agent_id,
        "title": new_thread.title,
        "description": new_thread.description,
        "create_at": new_thread.create_at.isoformat(),
        "update_at": new_thread.update_at.isoformat(),
    }


@chat.get("/threads", response_model=list[ThreadResponse])
async def list_threads(
        agent_id: str | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_required_user)
):
    """
    获取用户的所有对话线程

    参数:
        agent_id: 过滤特定智能体的线程
        db: 数据库会话
        current_user: 当前认证用户

    返回:
        list[ThreadResponse]: 线程列表
    """
    query = db.query(Thread).filter(
        Thread.user_id == current_user.id,
        Thread.status == 1
    )

    if agent_id:
        query = query.filter(Thread.agent_id == agent_id)

    threads = query.order_by(Thread.update_at.desc()).all()

    return [
        {
            "id": thread.id,
            "user_id": thread.user_id,
            "agent_id": thread.agent_id,
            "title": thread.title,
            "description": thread.description,
            "create_at": thread.create_at.isoformat(),
            "update_at": thread.update_at.isoformat(),
        }
        for thread in threads
    ]


@chat.delete("/thread/{thread_id}")
async def delete_thread(
        thread_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_required_user)
):
    """
    删除指定对话线程（软删除）

    参数:
        thread_id: 要删除的线程ID
        db: 数据库会话
        current_user: 当前认证用户

    返回:
        dict: 操作结果消息

    异常:
        若线程不存在返回404
    """
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == current_user.id
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail="对话线程不存在")

    # 软删除
    thread.status = 0
    db.commit()

    return {"message": "删除成功"}


class ThreadUpdate(BaseModel):
    """线程更新模型"""
    title: str | None = None
    description: str | None = None


@chat.put("/thread/{thread_id}", response_model=ThreadResponse)
async def update_thread(
        thread_id: str,
        thread_update: ThreadUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_required_user)
):
    """
    更新对话线程信息

    参数:
        thread_id: 要更新的线程ID
        thread_update: 更新内容
        db: 数据库会话
        current_user: 当前认证用户

    返回:
        ThreadResponse: 更新后的线程信息

    异常:
        若线程不存在返回404
    """
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == current_user.id,
        Thread.status == 1
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail="对话线程不存在")

    if thread_update.title is not None:
        thread.title = thread_update.title

    if thread_update.description is not None:
        thread.description = thread_update.description

    db.commit()
    db.refresh(thread)

    return {
        "id": thread.id,
        "user_id": thread.user_id,
        "agent_id": thread.agent_id,
        "title": thread.title,
        "description": thread.description,
        "create_at": thread.create_at.isoformat(),
        "update_at": thread.update_at.isoformat(),
    }
