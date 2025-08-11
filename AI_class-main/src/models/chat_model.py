import os
import requests
from openai import OpenAI
from src.utils import logger, get_docker_safe_url
from langchain_openai import ChatOpenAI


class OpenAIBase:
    """
    OpenAI API基础操作类，封装了与OpenAI兼容API的交互功能

    Args:
        api_key (str): API访问密钥
        base_url (str): API基础URL地址
        model_name (str): 使用的模型名称
        chat_open_ai (ChatOpenAI, optional): 预初始化的ChatOpenAI实例
        **kwargs: 其他模型相关信息
    """

    def __init__(self, api_key, base_url, model_name, chat_open_ai=None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        self.info = kwargs
        # 初始化LangChain的ChatOpenAI对象
        self.chat_open_ai = chat_open_ai or ChatOpenAI(model=model_name,
                                                       api_key=api_key,
                                                       base_url=base_url)

    def predict(self, message, stream=False):
        """
        生成模型预测结果

        Args:
            message (str/list): 输入消息，可以是字符串或消息字典列表
            stream (bool): 是否使用流式响应

        Returns:
            流式响应时返回生成器，非流式时返回完整响应消息
        """
        # 标准化输入消息格式
        if isinstance(message, str):
            messages = [{"role": "user", "content": message}]
        else:
            messages = message

        # 根据流式标志选择响应方式
        if stream:
            return self._stream_response(messages)
        else:
            return self._get_response(messages)

    def _stream_response(self, messages):
        """处理流式响应，逐块生成结果"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
            )
            # 迭代返回每个响应块
            for chunk in response:
                    if len(chunk.choices) > 0:
                        yield chunk.choices[0].delta

        except Exception as e:
            # 记录详细错误信息（隐藏完整API密钥）
            err = f"Error streaming response: {e}, URL: {self.base_url}, API Key: {self.api_key[:5]}***, Model: {self.model_name}"
            logger.error(err)
            raise Exception(err)

    def _get_response(self, messages):
        """获取完整非流式响应"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False,
        )
        return response.choices[0].message

    def get_models(self):
        """获取可用的文本模型列表"""
        try:
            return self.client.models.list(
                extra_query={
                    "type": "text"
                }
            )
        except Exception as e:
            logger.error(f"Error getting models: {e}")
            return []


class OpenModel(OpenAIBase):
    """OpenAI官方模型实现类"""

    def __init__(self, model_name=None):
        # 设置默认模型并读取环境变量
        model_name = model_name or "gpt-4o-mini"
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE")
        super().__init__(api_key=api_key, base_url=base_url, model_name=model_name)


class CustomModel(OpenAIBase):
    """自定义API端点模型实现类"""

    def __init__(self, model_info):
        # 从模型配置字典中提取参数
        model_name = model_info["name"]
        api_key = model_info.get("api_key") or "custom_model"
        # 获取Docker环境安全URL
        base_url = get_docker_safe_url(model_info["api_base"])
        logger.info(f"> Custom model: {model_name}, base_url: {base_url}")

        super().__init__(api_key=api_key, base_url=base_url, model_name=model_name)


class GeneralResponse:
    """通用响应对象容器"""

    def __init__(self, content):
        self.content = content
        self.is_full = False


class Qianfan(OpenAIBase):
    """百度千帆大模型API实现类（已弃用）"""

    def __init__(self, model_name="ernie_speed") -> None:
        import qianfan
        self.model_name = model_name
        # 从环境变量获取认证密钥
        access_key = os.getenv("QIANFAN_ACCESS_KEY")
        secret_key = os.getenv("QIANFAN_SECRET_KEY")
        self.client = qianfan.ChatCompletion(ak=access_key, sk=secret_key)

    def predict(self, message, stream=False):
        """覆写预测方法以适应千帆API"""
        # 标准化输入消息格式
        if isinstance(message, str):
            messages = [{"role": "user", "content": message}]
        else:
            messages = message

        # 路由到流式/非流式处理
        if stream:
            return self._stream_response(messages)
        else:
            return self._get_response(messages)

    def _stream_response(self, messages):
        """千帆API流式响应处理"""
        response = self.client.do(
            model=self.model_name,
            messages=messages,
            stream=True,
        )
        # 封装为通用响应对象
        for chunk in response:
            yield GeneralResponse(chunk["body"]["result"])

    def _get_response(self, messages):
        """千帆API非流式响应处理"""
        response = self.client.do(
            model=self.model_name,
            messages=messages,
            stream=False,
        )
        return GeneralResponse(response["body"]["result"])


class DashScope(OpenAIBase):
    """阿里云DashScope API实现类"""

    def __init__(self, model_name="qwen-max-latest") -> None:
        self.model_name = model_name
        self.api_key = os.getenv("DASHSCOPE_API_KEY")

    def predict(self, message, stream=False):
        """覆写预测方法以适应DashScope API"""
        # 标准化输入消息格式
        if isinstance(message, str):
            messages = [{"role": "user", "content": message}]
        else:
            messages = message

        # 路由到流式/非流式处理
        if stream:
            return self._stream_response(messages)
        else:
            return self._get_response(messages)

    def _stream_response(self, messages):
        """DashScope流式响应处理"""
        import dashscope
        response = dashscope.Generation.call(
            api_key=self.api_key,
            model=self.model_name,
            messages=messages,
            result_format='message',
            stream=True,
        )
        # 标记为部分响应并返回
        for chunk in response:
            message = chunk.output.choices[0].message
            message.is_full = False
            yield chunk.output.choices[0].message

    def _get_response(self, messages):
        """DashScope非流式响应处理"""
        import dashscope
        response = dashscope.Generation.call(
            api_key=self.api_key,
            model=self.model_name,
            messages=messages,
            result_format='message',
            stream=False,
        )
        return response.output.choices[0].message


if __name__ == "__main__":
    pass
