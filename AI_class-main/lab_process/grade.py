import os
import json
import logging
from typing import Dict, Optional, Any  # 更精确的类型提示

from dotenv import load_dotenv

# 导入 OpenAI 客户端 (基础库，用于直接与 OpenAI 兼容 API 交互)
from openai import OpenAI

# 获取一个 logger 实例
logger = logging.getLogger(__name__)

load_dotenv()

# --- 全局配置变量 (与之前保持一致) ---
DEFAULT_ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")
DEFAULT_ALIYUN_BASE_URL = os.getenv("ALIYUN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
# 评估模型通常使用通用文本模型，例如 qwen-max 或 qwen-turbo
DEFAULT_EVAL_MODEL = "qwen-vl-max"  # 或者 "qwen-turbo"

# 初始化 OpenAI 客户端，指向阿里云的兼容模式接口
# 注意：这里是模块级别的初始化，意味着如果 evaluate_response 函数内部不传入新的key/url
# 它会一直使用这个全局配置
client = OpenAI(
    api_key=DEFAULT_ALIYUN_API_KEY,
    base_url=DEFAULT_ALIYUN_BASE_URL,
)


def evaluate_response(
        predicted: str,
        groundtruth: str,
        api_key: str = None,  # 允许外部传入 API Key
        base_url: str = None,  # 允许外部传入 Base URL
        model: str = None  # 允许外部传入模型名称
) -> Dict[str, Any]:  # 返回类型注解为 Dict[str, Any] 更通用
    """
    使用阿里云通义千问模型评估模型生成结果与标准答案之间的一致性，
    返回包含分数与理由的字典。

    :param predicted: 模型生成的答案 (文本)
    :param groundtruth: 数据集中的真实答案 (文本)
    :param api_key: (可选) 阿里云 API Key。如果未提供，将尝试从环境变量获取。
    :param base_url: (可选) 阿里云 API 的基础 URL。如果未提供，将使用默认值。
    :param model: (可选) 指定使用的模型。如果未提供，将使用默认值（qwen-max）。
    :return: 包含 "score" 和 "justification" 的字典，如果出错则返回错误信息。
    """
    # 确定实际使用的 API Key, Base URL 和模型
    _api_key = api_key if api_key else DEFAULT_ALIYUN_API_KEY
    _base_url = base_url if base_url else DEFAULT_ALIYUN_BASE_URL
    _model = model if model else DEFAULT_EVAL_MODEL

    if not _api_key:
        return {"score": 0, "justification": "Error: ALIYUN_API_KEY is not provided."}

    # 为了支持函数参数动态覆盖，在函数内部重新实例化客户端
    current_client = OpenAI(
        api_key=_api_key,
        base_url=_base_url,
    )

    # 对输入字符串进行转义，以避免与 JSON 格式冲突
    # 这里使用 f-string 和双大括号来避免与 Python 格式化冲突，同时保留 JSON 模板的大括号
    prompt = f"""
你是一名 AI 模型响应的专业评估员。

给定:
- 模型的回复:
\"\"\"{predicted}\"\"\"

- 参考答案:
\"\"\"{groundtruth}\"\"\"

请评估模型回复与参考答案的一致性，如果选的答案一致，就给满分100，否则根据推理过程与参考给出合理分数，范围20到100
你需要给出详细的解释。
请以严格的 JSON 格式返回你的评估结果:
{{
    "score": <20到100之间的整数>,
    "justification": "<简洁的解释>"
}}
"""

    try:
        print(f"正在调用评估模型 {_model}...")
        response_content = current_client.chat.completions.create(
            model=_model,  # 使用动态指定的模型
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,  # 评估任务通常需要确定性结果，所以温度设为0
            response_format={"type": "json_object"}  # 明确要求 JSON 格式输出
        ).choices[0].message.content

        cleaned_content = response_content.strip()
        # 移除 Markdown 代码块的包裹符，如果存在
        if cleaned_content.startswith('```json'):
            cleaned_content = cleaned_content[len('```json'):].strip()
        if cleaned_content.endswith('```'):
            cleaned_content = cleaned_content[:-len('```')].strip()

        logger.info(f"Cleaned LLM response content before JSON parse: '{cleaned_content}'")

        # 解析LLM返回的JSON字符串
        evaluation_result = json.loads(cleaned_content)
        print("评估结果：", evaluation_result)

        # 验证 JSON 结构是否符合预期
        if not all(k in evaluation_result for k in ["score", "justification"]):
            raise ValueError("LLM response JSON is missing 'score' or 'justification' fields.")
        if not isinstance(evaluation_result["score"], (int, float)) or not (0 <= evaluation_result["score"] <= 100):
            raise ValueError("LLM response 'score' is not a valid integer between 0 and 100.")

        return evaluation_result

    except json.JSONDecodeError as e:
        error_message = f"Evaluation failed: LLM returned invalid JSON. Details: {e}. Raw content: '{cleaned_content}'"
        print(f"[evaluate_response] Error: {error_message}")
        return {"score": 0, "justification": error_message}
    except Exception as e:
        error_message = f"Evaluation failed due to error: {str(e)}"
        print(f"[evaluate_response] Error: {error_message}")
        # 在其他错误情况下也返回一个结构一致的字典
        return {"score": 0, "justification": error_message}


# --- 辅助函数 ---
def format_groundtruth_for_eval(gt_raw: str) -> str:
    """
    将原始 groundtruth json 格式解析为自然语言评价格式。
    """
    try:
        gt = json.loads(gt_raw)
        options = gt.get("options", [])
        correct_option = gt.get("answer")  # 例如 "C"
        question = gt.get("question")

        correct_answer_text = "N/A"
        if correct_option and options:
            # 找到正确选项对应的文本
            try:
                index = ord(correct_option.upper()) - ord("A")
                if 0 <= index < len(options):
                    correct_answer_text = options[index]
            except (TypeError, ValueError):
                pass  # 忽略非字母的correct_option

        return f"""正确答案是:

- {correct_answer_text}

解释:

问题是: "{question}"。在选项 {options} 中，正确答案是 {correct_answer_text} (选项 {correct_option})。"""
    except json.JSONDecodeError:
        return f"无法解析 groundtruth JSON: {gt_raw}"
    except Exception as e:
        return f"格式化 groundtruth 时出错: {e}. 原始数据: {gt_raw}"


def read_10th_line_from_jsonl(file_path: str) -> Optional[str]:
    """
    从 .jsonl 文件中读取第 10 行。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for i in range(9):  # 跳过前 9 行
                next(file, None)
            tenth_line = next(file, None)
            if tenth_line:
                return tenth_line.strip()
            else:
                print("文件不足 10 行。")
                return None
    except FileNotFoundError:
        print(f"文件未找到: {file_path}，请检查文件路径。")
        return None
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None


# --- 示例用法 ---
if __name__ == "__main__":
    predicted_response = """
    最好的答案是：

    - HENRI DE TOULOUSE-LAUTREC

    解释：

    推理结果表明，所讨论的艺术品名为“Jane Avril”，这是一张由 Henri de Toulouse-Lautrec 创作的著名海报。图像上发现的签名“H. Stern, Paris”很可能是印刷商或出版商的签名，而不是艺术家的。因此，“Jane Avril”艺术品的实际艺术家是 Henri de Toulouse-Lautrec。这与作品的已知历史及其创作者相符，使得 Henri de Toulouse-Lautrec 成为给定选项中的正确选择。
    """

    # 模拟从数据集读取的原始 groundtruth JSON 字符串
    # 假设这是第10行的内容
    raw_groundtruth_jsonl = """{"question": "Name the Artist", "options": ["CLAUDE MONET", "HENRI MATISSE", "HENRI DE TOULOUSE-LAUTREC", "EDOUARD MANET"], "answer": "C"}"""

    # 格式化 groundtruth 为评估模型可读的文本
    formatted_groundtruth = format_groundtruth_for_eval(raw_groundtruth_jsonl)

    print("--- 评估示例 ---")
    judge_result = evaluate_response(predicted_response, formatted_groundtruth)

    if "error" in judge_result:
        print(f"评估失败: {judge_result['error']}")
    else:
        print("\n最终评估结果:")
        print(f"分数: {judge_result.get('score', 'N/A')}")
        print(f"理由: {judge_result.get('justification', 'N/A')}")

    # 尝试从实际文件读取（如果存在）
    # test_file_path = "path/to/your/test_data.jsonl" # 请替换为你的实际文件路径
    # if os.path.exists(test_file_path):
    #     raw_gt_line = read_10th_line_from_jsonl(test_file_path)
    #     if raw_gt_line:
    #         formatted_gt_from_file = format_groundtruth_for_eval(raw_gt_line)
    #         print(f"\n从文件读取并格式化的 Groundtruth:\n{formatted_gt_from_file}")
    #         # 再次评估
    #         judge_result_from_file = evaluate_response(predicted_response, formatted_gt_from_file)
    #         print("\n从文件读取后的评估结果:")
    #         print(judge_result_from_file)
    # else:
    #     print(f"\n注意: 未找到测试文件 '{test_file_path}'，跳过文件读取示例。")