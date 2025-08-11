import os
import asyncio
import requests
from typing import List, Optional, AsyncGenerator
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 导入 LangChain 的 OpenAI 聊天模型封装
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAI  # 用于 describe_image 中直接调用 Qwen-VL-Max

# 确保加载环境变量，例如 .env 文件中的 ALIYUN_API_KEY
load_dotenv()

# --- 全局配置变量 ---
DEFAULT_ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")
DEFAULT_ALIYUN_BASE_URL = os.getenv("ALIYUN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DEFAULT_QWEN_VL_MODEL = "qwen-vl-max"  # 通义千问的视觉理解模型


# --------------- 1. 图像描述函数 (现在只接受 URL) ---------------

def describe_image(
        image_url: str,
        prompt: str = "Please use English to describe the image in detail, including the objects, actions, and relationships that everything you see in the image.",
        api_key: str = None,
        base_url: str = None,
        model: str = None
) -> str:
    """
    使用阿里云 Qwen-VL-Max 模型对指定 URL 的图片进行描述。
    **此函数现在只接受图片 URL，不进行本地下载或 Base64 编码。**

    :param image_url: 图片的 URL (必须是网络可访问的 URL)
    :param prompt: 自定义提示词，默认为描述图片的详细内容
    :param api_key: (可选) 阿里云 API Key。如果未提供，将尝试从环境变量获取。
    :param base_url: (可选) 阿里云 API 的基础 URL。如果未提供，将使用默认值。
    :param model: (可选) 指定使用的 Qwen-VL 模型。如果未提供，将使用默认值。
    :return: 图片的英文描述信息，或错误信息
    """
    _api_key = api_key if api_key else DEFAULT_ALIYUN_API_KEY
    _base_url = base_url if base_url else DEFAULT_ALIYUN_BASE_URL
    _model = model if model else DEFAULT_QWEN_VL_MODEL

    if not _api_key:
        return "Error: ALIYUN_API_KEY is not provided. Please set it in .env, environment variables, or pass it as an argument."

    try:
        # 1. 验证 image_url 格式
        if not image_url.startswith(('http://', 'https://')):
            return "Error: Invalid image_url format. Please provide a valid URL (http:// or https://)."

        # 2. 简单验证 URL 可访问性 (可选，但推荐)
        try:
            print(f"正在尝试验证图片 URL 可访问性: {image_url}")
            response = requests.head(image_url, timeout=10)
            response.raise_for_status()  # 如果状态码不是 2xx，则抛出异常
            if not response.headers.get('Content-Type', '').startswith('image/'):
                print(f"警告: URL 内容类型可能不是图片: {response.headers.get('Content-Type')}")
        except requests.exceptions.Timeout:
            print(f"URL 可访问性验证超时: {image_url}")
            return f"Error: Timeout when validating image URL from {image_url}. Please check the URL."
        except requests.exceptions.RequestException as e:
            print(f"URL 可访问性验证失败: {e}")
            return f"Error: Failed to validate image URL. {e}. Please check the URL."
        except Exception as e:
            print(f"验证 URL 时发生未知错误: {e}")
            return f"Error: An unexpected error occurred while validating the image URL. {e}"

        # 3. 初始化 OpenAI 客户端 (指向阿里云)
        client = OpenAI(
            api_key=_api_key,
            base_url=_base_url,
        )

        # 4. 创建请求
        completion = client.chat.completions.create(
            model=_model,
            messages=[
                {'role': 'user', 'content': [
                    {
                        'type': 'text',
                        'text': prompt
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': image_url,  # 直接传入图片 URL
                        }
                    }
                ]}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"处理图片描述时发生意外错误: {str(e)}")
        return f"Error: An unexpected error occurred while processing image description. {str(e)}"


# 如果需要流式描述，也可以保留此函数
async def describe_image_stream(
        image_url: str,
        prompt: str = "Please use English to describe the image in detail, including the objects, actions, and relationships that everything you see in the image.",
        api_key: str = None,
        base_url: str = None,
        model: str = None
) -> AsyncGenerator[str, None]:
    """
    使用阿里云 Qwen-VL-Max 模型对指定 URL 的图片进行描述，以流式方式返回结果。
    **此函数现在只接受图片 URL，不进行本地下载或 Base64 编码。**

    :param image_url: 图片的 URL (必须是网络可访问的 URL)
    :param prompt: 自定义提示词，默认为描述图片的详细内容
    :param api_key: (可选) 阿里云 API Key。如果未提供，将尝试从环境变量获取。
    :param base_url: (可选) 阿里云 API 的基础 URL。如果未提供，将使用默认值。
    :param model: (可选) 指定使用的 Qwen-VL 模型。如果未提供，将使用默认值。
    :yield: 图片描述的文本片段或错误信息
    """
    _api_key = api_key if api_key else DEFAULT_ALIYUN_API_KEY
    _base_url = base_url if base_url else DEFAULT_ALIYUN_BASE_URL
    _model = model if model else DEFAULT_QWEN_VL_MODEL

    if not _api_key:
        yield "Error: ALIYUN_API_KEY is not provided. Please set it in .env, environment variables, or pass it as an argument."
        return

    try:
        # 1. 验证 image_url 格式
        if not image_url.startswith(('http://', 'https://')):
            yield "Error: Invalid image_url format. Please provide a valid URL (http:// or https://)."
            return

        # 2. 简单验证 URL 可访问性 (可选，但推荐)
        try:
            print(f"正在尝试验证图片 URL 可访问性: {image_url}")
            response = requests.head(image_url, timeout=10)
            response.raise_for_status()
            if not response.headers.get('Content-Type', '').startswith('image/'):
                print(f"警告: URL 内容类型可能不是图片: {response.headers.get('Content-Type')}")
        except requests.exceptions.Timeout:
            print(f"URL 可访问性验证超时: {image_url}")
            yield f"Error: Timeout when validating image URL from {image_url}. Please check the URL."
            return
        except requests.exceptions.RequestException as e:
            print(f"URL 可访问性验证失败: {e}")
            yield f"Error: Failed to validate image URL. {e}. Please check the URL."
            return
        except Exception as e:
            print(f"验证 URL 时发生未知错误: {e}")
            yield f"Error: An unexpected error occurred while validating the image URL. {e}"
            return

        # 3. 初始化 OpenAI 客户端 (指向阿里云)
        client = OpenAI(
            api_key=_api_key,
            base_url=_base_url,
        )

        # 4. 创建流式请求
        stream = client.chat.completions.create(
            model=_model,
            messages=[
                {'role': 'user', 'content': [
                    {
                        'type': 'text',
                        'text': prompt
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': image_url,  # 直接传入图片 URL
                        }
                    }
                ]}
            ],
            stream=True
        )

        # 5. 逐步返回流式结果
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        print(f"处理图片描述时发生意外错误: {str(e)}")
        yield f"Error: An unexpected error occurred while processing image description. {str(e)}"


# --------------- 2. 规划器函数 ---------------

class Plan(BaseModel):
    """用于表示规划步骤的 Pydantic 模型"""
    steps: List[str] = Field(
        description="要遵循的不同步骤，应按排序顺序排列"
    )


def generate_plan(
        user_question: str,
        image_caption: str,
        system_prompt: Optional[str] = None,
        model_name: str = DEFAULT_QWEN_VL_MODEL,  # 默认使用 Qwen-VL 模型
        temperature: float = 0.0,
        api_key: str = None,  # 允许外部传入 API Key
        base_url: str = None  # 允许外部传入 Base URL
) -> Optional[Plan]:
    """
    根据图像描述和问题生成推理步骤计划。

    此函数通过 LangChain 的 ChatOpenAI 封装器调用阿里云通义千问模型。

    :param user_question: 用户的问题
    :param image_caption: 图像的描述
    :param system_prompt: 可选的系统提示词
    :param model_name: 使用的 LLM 模型名称，默认为 Qwen-VL-Max
    :param temperature: 模型采样温度
    :param api_key: (可选) 阿里云 API Key。如果未提供，将尝试从环境变量获取。
    :param base_url: (可选) 阿里云 API 的基础 URL。如果未提供，将使用默认值。
    :return: Plan 对象（包含步骤），出错返回 None
    """
    # 确定实际使用的 API Key 和 Base URL
    _api_key = api_key if api_key else DEFAULT_ALIYUN_API_KEY
    _base_url = base_url if base_url else DEFAULT_ALIYUN_BASE_URL

    if not _api_key:
        print("Error: 未提供 ALIYUN_API_KEY。请在 .env 文件、环境变量中设置，或作为参数传入。")
        return None

    if system_prompt is None:
        system_prompt = (
            "你是一个视觉推理任务的专家规划师。你的工作是将给定的问题分解为一步一步的计划。"
            "请使用提供的图像描述作为上下文。每一步都应该是独立的、精确的，并直接有助于回答问题。"
            "避免不必要的步骤。你不需要给出最终答案。"
        )

    # 构造 Prompt 模板
    planner_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{full_prompt}")
    ])

    # 使用 LangChain 的 ChatOpenAI，但指向阿里云的兼容模式接口
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        openai_api_key=_api_key,  # LangChain ChatOpenAI 使用 openai_api_key
        openai_api_base=_base_url  # LangChain ChatOpenAI 使用 openai_api_base
    )

    # 构造链
    planner_chain = planner_prompt | llm.with_structured_output(Plan)

    # 构造实际输入
    full_prompt = (
        f"图像显示：{image_caption}\n\n"
        f"基于此图像，通过构建一个计划来回答以下问题：\n"
        f"{user_question}"
    )

    try:
        print(f"正在调用模型 {model_name}...")
        return planner_chain.invoke({"full_prompt": full_prompt})
    except Exception as e:
        print(f"[generate_plan] 调用模型时出错: {str(e)}")
        if "AuthenticationError" in str(e) or "invalid api_key" in str(e).lower():
            print("请检查您的 API Key 是否正确并有效。")
        elif "Cannot connect to host" in str(e) or "Connection refused" in str(e):
            print("请检查网络连接或 base_url 是否正确。")
        return None


# --------------- 示例用法 ---------------
if __name__ == "__main__":
    # 请确保您有一个可访问的图片 URL
    # 例如：
    image_to_process_url = "https://modelscope.cn/datasets/modelscope/MMMU-Reasoning-Distill-Validation/resolve/master/images/validation_Literature_24_1.png"

    print(f"正在获取图片描述 (URL: {image_to_process_url})...")
    # 直接传入 URL 给 describe_image
    image_caption = describe_image(image_to_process_url)

    if "Error:" in image_caption:
        print(f"获取图片描述失败: {image_caption}")
    else:
        print(f"图片描述: {image_caption[:150]}...")  # 打印部分描述
        user_query = "Refer to the figure, which term best describes the dynamics of children and their relationships with parents and siblings?。"
        print(f"\n用户问题: {user_query}")

        # 调用 generate_plan
        plan = generate_plan(user_query, image_caption)

        if plan:
            print("\n生成的计划:")
            for i, step in enumerate(plan.steps):
                print(f"步骤 {i + 1}: {step}")
        else:
            print("\n未能生成计划。")