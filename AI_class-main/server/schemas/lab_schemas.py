from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

# Pydantic 模型定义了API请求和响应的数据结构、类型和验证规则。

class SetPendingByIdRequest(BaseModel):
    """用于通过ID设置实验为pending状态的请求体。"""
    experiment_id: str = Field(alias="id", description="要设置为pending状态的实验ID")

class ResetAllExperimentsRequest(BaseModel):
    """用于重置所有实验为pending状态的请求体。"""
    confirm: bool = Field(description="确认重置所有实验状态")

# --- 实验步骤相关 ---
class CompleteByImageUrlRequest(BaseModel):
    """用于通过图片URL完成实验状态并记录分数的请求体。"""
    image_url: str = Field(description="实验关联的图片URL")
    score: Optional[Union[float, int, str]] = Field(None, description="实验的分数，可以是数字或字符串")

class ImageCaptionRequest(BaseModel):
    """请求图像描述的请求体。"""
    image_path: str = Field(description="需要描述的图片的路径或URL")
    prompt: Optional[str] = Field(None, description="可选的，指导图像描述生成的提示")

class Plan(BaseModel):
    """表示一个实验计划，包含多个步骤。"""
    steps: List[str] = Field(description="按顺序排列的实验步骤列表")

class PlanGenerationRequest(BaseModel):
    """请求生成实验计划的请求体。"""
    user_question: str = Field(description="用户提出的原始问题或实验目标")
    image_caption: str = Field(description="相关图片的描述信息")
    system_prompt: Optional[str] = Field(None, description="可选的，指导计划生成的系统级提示")

class PlanRequest(BaseModel):
    """执行计划步骤的请求体。"""
    plan_list: List[str] = Field(description="要执行的计划步骤列表")
    image_caption: str = Field(description="相关图片的描述信息")

class AnswerRequest(BaseModel):
    """请求决策最终答案的请求体。"""
    reasoning_summary: str = Field(description="基于先前步骤的推理摘要")
    question: str = Field(description="需要回答的问题")
    options: List[str] = Field(description="问题相关的选项列表")

class EvaluateRequest(BaseModel):
    """请求评估实验响应的请求体。"""
    predicted: str = Field(description="模型或实验预测的答案/结果")
    groundtruth: str = Field(description="标准的、正确的答案/结果")

# 关于 ExperimentSchema 的说明:
# 如果 db_manage.schemas 中已定义了与此处交互式实验匹配的 ExperimentSchema，
# 优先考虑从那里导入并复用，以保持数据模型的一致性。
# 例如: from db_manage.schemas import ExperimentSchema