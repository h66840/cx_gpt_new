import os
import json
import re  # <--- 引入正则表达式模块
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

# --- 全局配置变量 (与之前保持一致) ---
DEFAULT_ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")
DEFAULT_ALIYUN_BASE_URL = os.getenv("ALIYUN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DEFAULT_DECIDER_MODEL = "qwen-vl-max"

# --- 决策器 LLM 初始化 (与之前保持一致) ---
decider_llm = ChatOpenAI(
    model=DEFAULT_DECIDER_MODEL,
    temperature=0,
    openai_api_key=DEFAULT_ALIYUN_API_KEY,
    openai_api_base=DEFAULT_ALIYUN_BASE_URL
)

# --- 决策器 Prompt 模板 (与之前保持一致) ---
decider_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "你是一个多项选择推理助手。请根据下面提供的推理结果来帮助正确回答问题。"),
    ("placeholder", "{messages}")
])

# 将 Prompt 模板与 LLM 组合成链
decider_chain = decider_prompt | decider_llm


# <--- 新增的辅助函数，用于从模型返回的文本中提取 JSON 字符串 ---
def _extract_json_string(text: str) -> str:
    """
    从可能包含 Markdown 代码块的文本中提取纯净的 JSON 字符串。
    例如，将 '```json\n{"key": "value"}\n```' 转换为 '{"key": "value"}'。
    """
    # 使用正则表达式查找被 ``` 包裹的内容，(?s) 标志让 . 匹配换行符
    match = re.search(r"```(?:json)?\s*({.*})\s*```", text, re.DOTALL)
    if match:
        # 如果找到匹配项，返回第一个捕获组（即花括号内的内容）
        return match.group(1).strip()

    # 如果没有找到 markdown 块，可能整个字符串就是 JSON，或者 JSON 混杂在文本中
    # 尝试寻找第一个 '{' 到最后一个 '}' 的部分
    start_index = text.find('{')
    end_index = text.rfind('}')
    if start_index != -1 and end_index != -1 and end_index > start_index:
        return text[start_index:end_index + 1]

    # 如果以上方法都失败，返回原始字符串（去除首尾空格）让后续的json.loads尝试处理
    return text.strip()


def decide_answer(
        reasoning_summary: str,
        question: str,
        options: list[str],
        api_key: str = None,
        base_url: str = None,
        model: str = None
) -> dict:
    """
    根据推理总结、问题和选项，决策出最佳答案并给出解释。
    此函数现在能处理模型返回的、被 Markdown 包裹的 JSON。
    """
    _api_key = api_key if api_key else DEFAULT_ALIYUN_API_KEY
    _base_url = base_url if base_url else DEFAULT_ALIYUN_BASE_URL
    _model = model if model else DEFAULT_DECIDER_MODEL

    if not _api_key:
        return {
            "error": "ALIYUN_API_KEY is not provided. Please set it in .env, environment variables, or pass it as an argument."}

    current_decider_llm = ChatOpenAI(
        model=_model,
        temperature=0,
        openai_api_key=_api_key,
        openai_api_base=_base_url
    )
    current_decider_chain = decider_prompt | current_decider_llm

    options_formatted = "\n".join([f"- {opt}" for opt in options])
    user_prompt = (
        f"推理结果:\n{reasoning_summary}\n\n"
        f"问题:\n{question}\n\n"
        f"选项:\n{options_formatted}\n\n"
        f"基于推理结果，选择最佳答案并解释您的选择。"
        f"请仅以 JSON 格式回复，包含 'answer' 和 'explanation' 两个字段。例如: "
        f'{{"answer": "选项", "explanation": "您的解释"}}'
    )

    try:
        print(f"正在调用决策模型 {_model}...")
        result = current_decider_chain.invoke({"messages": [HumanMessage(content=user_prompt)]})

        # <--- 核心改进：在解析前先清理和提取 JSON 字符串 ---
        print(f"模型原始返回: {result.content}")
        json_string = _extract_json_string(result.content)

        try:
            # 尝试解析清理后的字符串
            return json.loads(json_string)
        except json.JSONDecodeError:
            # 如果清理后仍然失败，打印更有用的错误信息
            print(f"警告: 清理后的字符串仍然不是有效的 JSON 格式: '{json_string}'")
            return {"answer": "N/A", "explanation": f"模型返回格式错误 (已尝试清理): {result.content}"}

    except Exception as e:
        print(f"[decide_answer] 调用模型时出错: {str(e)}")
        if "AuthenticationError" in str(e) or "invalid api_key" in str(e).lower():
            print("请检查您的 API Key 是否正确并有效。")
        elif "Cannot connect to host" in str(e) or "Connection refused" in str(e):
            print("请检查网络连接或 base_url 是否正确。")
        return {"error": f"An unexpected error occurred: {str(e)}"}


# --- 示例用法 (与之前保持一致) ---
if __name__ == "__main__":
    reasoning_summary = """
步骤: 识别图片中艺术家签名的位置。
输出: 艺术家的签名 "H. Stern, Paris" 垂直位于图像的右侧。

步骤: 阅读签名以确定艺术家的名字。
输出: 图像右侧的签名显示 "H. Stern, Paris"，表明艺术家的名字是 H. Stern。

步骤: 通过与作品标题“Jane Avril”和已知创作者进行交叉引用来验证名字。
输出: 交叉引用作品标题“Jane Avril”与已知创作者后发现，著名的 Jane Avril 海报是由 Henri de Toulouse-Lautrec 创作的，他是一位以描绘巴黎夜生活而闻名的法国艺术家。

因此，签名 "H. Stern, Paris" 可能指的是印刷商或出版商，而不是艺术家。作品“Jane Avril”的实际艺术家是 Henri de Toulouse-Lautrec。"""

    question = "请说出艺术家的名字。"
    options = ["CLAUDE MONET", "HENRI MATISSE", "HENRI DE TOULOUSE-LAUTREC", "EDOUARD MANET"]

    print("--- 决策答案示例 ---")
    answer = decide_answer(reasoning_summary, question, options)

    if "error" in answer:
        print(f"决策失败: {answer['error']}")
    else:
        print(f"\n--- 最终结果 ---")
        print(f"答案: {answer.get('answer', 'N/A')}")
        print(f"解释: {answer.get('explanation', 'N/A')}")