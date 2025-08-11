# server/routers/experiment_router.py

import json
from datetime import datetime
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from pydantic import BaseModel, Field

# 模仿您的导入结构
from server.utils.auth_middleware import get_required_user, get_admin_user, get_db
from server.models.user_model import User

from server.models.experiment_model import (
    Course,
    Experiment,
    ExperimentStep,
    Review,
    ExperimentRecord,
    ExperimentStatus
)
from src.utils.logging_config import logger

# --- 创建新的路由器 ---
exp_router = APIRouter(prefix="/experiments", tags=["Experiments"])


# --- Pydantic 模型定义 (用于请求体) ---

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None


class ExperimentCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    tag: Optional[str] = None
    image: Optional[str] = None
    course_id: int


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str
    aspect_ratings: Optional[Dict[str, int]] = None


class AnswersSubmit(BaseModel):
    answers: Dict[int, str]


class ExperimentStepStatus(BaseModel):
    id: int
    step_number: int
    question: str
    image_path: Optional[str] = None
    image_description: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    status: str = Field(...,
                        description="Status of this specific step for the current user's record (e.g., 'pending', 'completed', 'failed', 'answered')")
    score: float = Field(0.0, description="Score for this specific step, if applicable")
    user_answer: Optional[str] = Field(None, description="User's submitted answer for this step")


class ExperimentRecordDetails(BaseModel):
    id: int
    user_id: int
    experiment_id: int
    status: ExperimentStatus
    score: float
    start_time: datetime
    end_time: Optional[datetime] = None
    steps_status: List[ExperimentStepStatus] = Field([], description="Detailed status for each step in the experiment")


class ExperimentRecordComplete(BaseModel):
    user_id: int
    experiment_id: int
    current_step_id: int = Field(..., description="要完成的实验步骤ID")
    score: float = Field(..., ge=0.0, le=100.0)


# --- API 路由 ---



# ==================== 普通用户操作接口 ====================
@exp_router.get("/courses")
async def get_all_courses(
        current_user: User = Depends(get_required_user),
        db: Session = Depends(get_db)
):
    """获取所有可用的课程列表，无论用户是否订阅"""
    try:
        courses = db.query(Course).all()
        return [course.to_dict() for course in courses]
    except Exception as e:
        logger.error(f"用户 {current_user.username} 获取所有课程列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取课程列表失败")


@exp_router.get("/course/{course_id}/experiments")
async def get_experiments_in_course(
        course_id: int,
        current_user: User = Depends(get_required_user),
        db: Session = Depends(get_db)
):
    """获取指定课程下的所有实验卡片列表"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    experiments = db.query(Experiment).filter(Experiment.course_id == course_id).all()
    return [exp.to_dict() for exp in experiments]


@exp_router.get("/{experiment_id}")
async def get_experiment_details(
        experiment_id: int,
        current_user: User = Depends(get_required_user),
        db: Session = Depends(get_db)
):
    """获取单个实验的详细信息，包括步骤和评论"""
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    response_dict = experiment.to_dict()

    response_dict["curriculum"] = [step.to_dict(include_answer=False) for step in experiment.steps]

    reviews = db.query(Review).filter(Review.experiment_id == experiment_id).order_by(Review.timestamp.desc()).all()
    response_dict["reviews"] = [review.to_dict() for review in reviews]

    if reviews:
        total_rating = sum(r.rating for r in reviews if r.rating is not None)
        response_dict["overall_rating"] = round(total_rating / len(reviews), 1)
    else:
        response_dict["overall_rating"] = 0.0

    return response_dict


@exp_router.post("/{experiment_id}/reviews", status_code=status.HTTP_201_CREATED)
async def submit_review(
        experiment_id: int,
        review_data: ReviewCreate,
        current_user: User = Depends(get_required_user),
        db: Session = Depends(get_db)
):
    """为某个实验提交一条评论"""
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="无法评论一个不存在的实验")

    new_review = Review(
        **review_data.model_dump(),
        user_id=current_user.id,
        experiment_id=experiment_id
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review.to_dict()



@exp_router.post("/{experiment_id}/step/{step_id}/start")
async def start_or_continue_step(
        experiment_id: int,
        step_id: int,
        current_user: User = Depends(get_required_user),
        db: Session = Depends(get_db)
):
    """
    用户开始或继续一个具体的实验步骤。
    如果该步骤已有记录，则更新其状态为进行中；如果没有，则创建新记录。
    返回该步骤的记录信息，并包含当前步骤的正确答案和解释。
    """
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        logger.error(f"实验 {experiment_id} 不存在。")
        raise HTTPException(status_code=404, detail="实验不存在")

    target_step = db.query(ExperimentStep).filter(
        ExperimentStep.id == step_id, # 使用 step_id
        ExperimentStep.experiment_id == experiment_id
    ).first()
    if not target_step:
        logger.error(f"步骤ID {step_id} 不存在或不属于实验 {experiment_id}。")
        raise HTTPException(status_code=404, detail=f"步骤ID {step_id} 不存在或不属于实验 {experiment_id}")

    record = db.query(ExperimentRecord).filter_by(
        user_id=current_user.id,
        experiment_id=experiment_id,
        current_step_id=step_id  # 筛选出当前点击步骤的记录
    ).first()

    if record:
        if record.status == ExperimentStatus.COMPLETED:
            logger.info(f"用户 {current_user.username} 尝试开始已完成的步骤 {step_id} (记录 {record.id})。")
            # 如果已完成，返回现有记录信息
            response_record_data = record.to_dict()
        else:
            # 如果未开始或进行中，更新状态为进行中，更新开始时间
            record.status = ExperimentStatus.IN_PROGRESS
            record.start_time = datetime.now()
            try:
                db.commit()
                db.refresh(record)
                logger.info(f"用户 {current_user.username} 继续进行中的步骤 {step_id} (记录 {record.id})。")
                response_record_data = record.to_dict()
            except Exception as e:
                db.rollback()
                logger.error(f"更新进行中步骤 {step_id} 记录失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"更新步骤记录失败: {e}")
    else:
        # 如果没有找到该步骤的记录，创建新记录
        new_record = ExperimentRecord(
            user_id=current_user.id,
            experiment_id=experiment_id,
            status=ExperimentStatus.IN_PROGRESS,
            score=0.0,
            answers=None, # 用户答案初始为空
            start_time=datetime.now(),
            end_time=None,
            current_step_id=step_id
        )
        db.add(new_record)
        try:
            db.commit()
            db.refresh(new_record)
            logger.info(f"用户 {current_user.username} 首次开始实验 {experiment_id} 的步骤 {step_id}，创建新记录: {new_record.id}")
            response_record_data = new_record.to_dict()
        except Exception as e:
            db.rollback()
            logger.error(f"创建新步骤 {step_id} 记录失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"创建新步骤记录失败: {e}")

    # 将 target_step 的 answer 和 explanation 添加到响应中

    response_record_data['answers'] = target_step.answer
    response_record_data['explanation'] = target_step.explanation

    # 返回完整的响应结构
    return {"message": "步骤操作成功。", "record": response_record_data}
@exp_router.get("/{experiment_id}/steps")
async def get_experiment_steps(
        experiment_id: int,
        current_user: User = Depends(get_required_user),
        db: Session = Depends(get_db)
):
    """
    获取指定实验下的所有实验步骤。
    此接口返回的步骤不包含正确答案，除非是管理员。
    """
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    include_answer = current_user.is_admin if hasattr(current_user, 'is_admin') else False

    steps = db.query(ExperimentStep).filter(ExperimentStep.experiment_id == experiment_id).all()

    logger.info(f"用户 {current_user.username} 获取实验 {experiment_id} 的所有步骤 (包含答案: {include_answer})")
    return [step.to_dict(include_answer=include_answer) for step in steps]

@exp_router.get("/{experiment_id}/record_details", response_model=ExperimentRecordDetails)
async def get_experiment_record_details(
        experiment_id: int,
        current_user: User = Depends(get_required_user),
        db: Session = Depends(get_db)
):
    """
    获取当前用户在指定整体实验下的所有步骤的执行详情。
    它会查找每个步骤对应的 ExperimentRecord，并汇总其状态和分数。
    """
    logger.debug(f"进入 get_experiment_record_details，整体实验ID: {experiment_id}, 用户ID: {current_user.id}")

    experiment = db.query(Experiment).options(joinedload(Experiment.steps)).filter(
        Experiment.id == experiment_id).first()
    if not experiment:
        logger.warning(f"实验 {experiment_id} 不存在。")
        raise HTTPException(status_code=404, detail="实验不存在")

    all_steps = sorted(experiment.steps, key=lambda s: s.id) # 获取所有步骤
    logger.debug(f"实验 {experiment_id} 共有 {len(all_steps)} 个步骤。")

    # 获取该用户在该整体实验下的所有步骤记录
    all_step_records = db.query(ExperimentRecord).filter(
        ExperimentRecord.user_id == current_user.id,
        ExperimentRecord.experiment_id == experiment_id
    ).all()

    # 将步骤记录按 step_id 映射，方便查找
    step_records_map = {record.current_step_id: record for record in all_step_records}

    steps_status_list = []
    total_score = 0.0
    completed_steps_count = 0

    for step in all_steps:
        step_status: str = "pending"
        step_score: float = 0.0
        user_answer: Optional[str] = None # 如果您选择在 ExperimentRecord.answers 中存储用户答案

        # 查找当前步骤对应的 ExperimentRecord
        record_for_this_step = step_records_map.get(step.id)

        if record_for_this_step:
            step_status = record_for_this_step.status.value
            step_score = record_for_this_step.score
            user_answer = record_for_this_step.answers # 获取该步骤的用户答案
            if record_for_this_step.status == ExperimentStatus.COMPLETED:
                completed_steps_count += 1
            total_score += step_score # 累加总分
            logger.debug(f"步骤 {step.id}: 找到记录 {record_for_this_step.id}，状态 '{step_status}', 分数 {step_score}")
        else:
            logger.debug(f"步骤 {step.id}: 未找到对应记录，默认为 'pending', 分数 0.0")

        steps_status_list.append(ExperimentStepStatus(
            id=step.id,
            step_number=step.id, # 假设 step_number 就是 id
            question=step.question,
            image_path=step.image_path,
            image_description=step.image_description,
            options=json.loads(step.options) if step.options and isinstance(step.options, str) else step.options,
            status=step_status,
            score=step_score,
            user_answer=user_answer
        ))

    # 汇总整个实验的 status 和 score
    overall_status = ExperimentStatus.NOT_STARTED
    if len(all_steps) > 0:
        if completed_steps_count == len(all_steps):
            overall_status = ExperimentStatus.COMPLETED
        elif completed_steps_count > 0:
            overall_status = ExperimentStatus.IN_PROGRESS # 至少有一个步骤完成了，但不是所有
        elif any(record.status == ExperimentStatus.IN_PROGRESS for record in all_step_records):
            overall_status = ExperimentStatus.IN_PROGRESS # 至少有一个步骤在进行中
        else:

            overall_status = ExperimentStatus.NOT_STARTED # 默认



    return ExperimentRecordDetails(
        id=-1,
        user_id=current_user.id,
        experiment_id=experiment_id,
        status=overall_status, # 整体实验状态
        score=total_score, # 整体实验总分
        start_time=datetime.min, # 占位符
        end_time=None, # 只有当整体状态为 COMPLETED 时才会有真实 end_time
        steps_status=steps_status_list
    )

@exp_router.post("/records/complete", status_code=status.HTTP_200_OK)
async def complete_experiment_record(
        record_data: ExperimentRecordComplete, # 使用更新后的 Pydantic 模型
        current_user: User = Depends(get_required_user),
        db: Session = Depends(get_db)
):
    """
    标记一个用户特定实验步骤的记录为已完成，并更新最终得分和结束时间。
    前端传入 user_id, experiment_id, score, 和 必需的 current_step_id。
    """
    logger.info(f"用户 {current_user.username} 请求完成实验步骤记录，数据: {record_data.model_dump()}")

    if record_data.user_id != current_user.id:
        logger.warning(f"用户 {current_user.username} 尝试修改其他用户 ({record_data.user_id}) 的实验记录。")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此实验记录，只能操作自己的记录。"
        )


    record = db.query(ExperimentRecord).filter(
        ExperimentRecord.user_id == record_data.user_id,
        ExperimentRecord.experiment_id == record_data.experiment_id,
        ExperimentRecord.current_step_id == record_data.current_step_id # 明确指定步骤ID
    ).first()

    if not record:
        logger.error(f"未找到用户 {record_data.user_id} 在实验 {record_data.experiment_id} 下步骤 {record_data.current_step_id} 的记录。")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到实验步骤 {record_data.current_step_id} 的对应记录。请确保该步骤有未开始或进行中的记录。"
        )

    # 如果记录已经是完成状态，可以根据业务逻辑决定是否允许重复更新分数
    if record.status == ExperimentStatus.COMPLETED:
        logger.warning(f"用户 {current_user.username} 尝试重复完成已完成的实验步骤记录 {record.id}。")

        pass

    # 更新记录的状态、分数和结束时间
    record.status = ExperimentStatus.COMPLETED
    record.score = record_data.score
    record.end_time = datetime.now()



    try:
        db.commit()
        db.refresh(record)
        logger.info(f"用户 {current_user.username} 成功完成实验步骤记录 {record.id} (步骤: {record.current_step_id})，得分: {record.score}")
        return {"message": "实验步骤记录已成功更新为完成状态。", "record": record.to_dict()}
    except Exception as e:
        db.rollback()
        logger.error(f"保存实验步骤记录 {record.id} 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存实验步骤记录时发生服务器错误: {e}"
        )
