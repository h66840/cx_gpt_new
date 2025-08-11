import os
from openai import OpenAI
from dotenv import load_dotenv
import asyncio
from typing import AsyncGenerator
import requests

# 在模块加载时就加载环境变量，确保全局配置可用
load_dotenv()


DEFAULT_ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")
DEFAULT_ALIYUN_BASE_URL = os.getenv("ALIYUN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DEFAULT_QWEN_VL_MODEL = "qwen-vl-max"

async def describe_image_stream(
    image_url: str,
    prompt: str = "Please use English to describe the image in detail, including the objects, actions, and relationships that everything you see in the image.",
    api_key: str = None,
    base_url: str = None,
    model: str = None
) -> AsyncGenerator[str, None]:
    """
    使用阿里云 Qwen-VL-Max 模型对指定 URL 的图片进行描述，以流式方式返回结果。
    直接传入图片 URL，不进行本地下载或 Base64 编码。

    :param image_url: 图片的 URL (必须是网络可访问的 URL)
    :param prompt: 自定义提示词，默认为描述图片的详细内容
    :param api_key: (可选) 阿里云 API Key。如果未提供，将尝试从环境变量 ALIYUN_API_KEY 获取。
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

        # 3. 初始化 OpenAI 客户端
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
                            'url': image_url,
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

def describe_image(
    image_url: str,
    prompt: str = "Please use English to describe the image in detail, including the objects, actions, and relationships that everything you see in the image.",
    api_key: str = None,
    base_url: str = None,
    model: str = None
) -> str:
    """
    使用阿里云 Qwen-VL-Max 模型对指定 URL 的图片进行描述。
    直接传入图片 URL，不进行本地下载或 Base64 编码。

    :param image_url: 图片的 URL (必须是网络可访问的 URL)
    :param prompt: 自定义提示词，默认为描述图片的详细内容
    :param api_key: (可选) 阿里云 API Key。如果未提供，将尝试从环境变量 ALIYUN_API_KEY 获取。
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
            response.raise_for_status()
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

        # 3. 初始化 OpenAI 客户端
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
                            'url': image_url,
                        }
                    }
                ]}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"处理图片描述时发生意外错误: {str(e)}")
        return f"Error: An unexpected error occurred while processing image description. {str(e)}"

# --- 示例用法 ---
async def example_stream_usage():
    image_url = 'https://modelscope.cn/datasets/modelscope/MMMU-Reasoning-Distill-Validation/resolve/master/images/validation_Literature_24_1.png'
    prompt = "请使用中文详细描述图片内容，包括您看到的物体、动作和它们之间的关系。"

    print("开始流式获取图片描述...")
    full_result = ""
    try:
        # 调用时可以不传 api_key 等，函数会尝试从环境变量获取
        async for chunk in describe_image_stream(image_url, prompt):
            print(chunk, end="", flush=True)
            full_result += chunk
        print("\n流式描述完成！")
    except Exception as e:
        print(f"\n流式处理过程中发生错误: {e}")

if __name__ == "__main__":


    print("\n--- 流式描述结果示例 ---")
    asyncio.run(example_stream_usage())

    print("\n--- 非流式描述结果示例 ---")
    image_url_non_stream = 'https://modelscope.cn/datasets/modelscope/MMMU-Reasoning-Distill-Validation/resolve/master/images/validation_Agriculture_16_1.png'
    prompt_non_stream = "这张图片展示了什么农业场景？"
    result_non_stream = describe_image(image_url_non_stream, prompt_non_stream)
    print(result_non_stream)