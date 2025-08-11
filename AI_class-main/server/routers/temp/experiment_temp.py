# server/routers/experiment_router.py

import json
from datetime import datetime
from typing import List, Optional, Dict, Union, Any

from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
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
    current_step_id: Optional[int] = None
    score: float = Field(..., ge=0.0, le=100.0)


# --- API 路由 ---

# ==================== 管理员操作接口 ====================

@exp_router.post("/courses", status_code=status.HTTP_201_CREATED)
async def create_course(
        course_data: CourseCreate,
        current_user: User = Depends(get_admin_user),
        db: Session = Depends(get_db)
):
    """(管理员) 创建一个新课程"""
    new_course = Course(**course_data.model_dump())
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    logger.info(f"管理员 {current_user.username} 创建了课程: {new_course.title}")
    return new_course.to_dict()


@exp_router.post("/assign-course-to-user")
async def assign_course_to_user(
        user_id: int = Body(..., embed=True),
        course_id: int = Body(..., embed=True),
        current_user: User = Depends(get_admin_user),
        db: Session = Depends(get_db)
):
    """(管理员) 为指定用户分配课程"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail=f"课程ID {course_id} 不存在")

    if course in user.subscribed_courses:
        raise HTTPException(status_code=400, detail="用户已订阅此课程")

    user.subscribed_courses.append(course)
    db.commit()
    logger.info(f"管理员 {current_user.username} 为用户 {user.username} 分配了课程 {course.title}")
    return {"message": "课程分配成功"}


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


@exp_router.post("/{experiment_id}/start/{current_step_id}")
async def start_experiment(
        experiment_id: int,
        current_step_id: int,
        current_user: User = Depends(get_required_user),
        db: Session = Depends(get_db)
):
    """
    开始或继续一个实验，并指定从哪个步骤开始。
    智能地处理实验记录的创建或更新，确保分数和状态的延续。
    当实验记录状态为 'COMPLETED' 时，会直接返回该记录，不会重置分数。
    返回的记录中，'answers' 和 'explanation' 字段将被填充为当前步骤的正确答案和解释。
    """
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    target_step = db.query(ExperimentStep).filter(
        ExperimentStep.id == current_step_id,
        ExperimentStep.experiment_id == experiment_id
    ).first()
    if not target_step:
        raise HTTPException(status_code=404, detail=f"步骤ID {current_step_id} 不存在或不属于实验 {experiment_id}")

    record = db.query(ExperimentRecord).filter_by(
        user_id=current_user.id,
        experiment_id=experiment_id
    ).order_by(desc(ExperimentRecord.start_time)).first()

    response_data = {}  # 初始化 response_data

    if record:
        if record.status == ExperimentStatus.COMPLETED:
            # 如果是已完成的记录，我们直接返回它，不创建新记录，不重置分数。
            # 仅仅更新当前步骤ID，以便前端知道用户现在在哪个步骤上。
            record.current_step_id = current_step_id
            db.commit()
            db.refresh(record)
            logger.info(
                f"用户 {current_user.username} 尝试开始已完成的实验 {experiment.title}。返回现有记录 {record.id}，分数 {record.score} 不变，当前步骤ID更新为: {record.current_step_id}")
            response_data = record.to_dict()
        elif record.status == ExperimentStatus.NOT_STARTED:
            # 如果是未开始的记录，将其状态改为进行中并更新当前步骤。分数保持 0.0。
            record.status = ExperimentStatus.IN_PROGRESS
            record.current_step_id = current_step_id
            db.commit()
            db.refresh(record)
            logger.info(
                f"用户 {current_user.username} 开始未开始的实验 {experiment.title}，更新记录 {record.id}，当前步骤ID为: {record.current_step_id}")
            response_data = record.to_dict()
        elif record.status == ExperimentStatus.IN_PROGRESS:
            # 如果是进行中的记录，直接更新当前步骤ID。分数保持不变。
            record.current_step_id = current_step_id
            db.commit()
            db.refresh(record)
            logger.info(
                f"用户 {current_user.username} 继续进行中的实验 {experiment.title}，更新记录 {record.id}，当前步骤ID为: {record.current_step_id}")
            response_data = record.to_dict()
    else:
        # 如果没有找到任何记录，说明是第一次开始，创建新记录
        new_record = ExperimentRecord(
            user_id=current_user.id,
            experiment_id=experiment_id,
            status=ExperimentStatus.IN_PROGRESS,
            score=0.0,  # 首次开始，分数为0
            answers=None,
            start_time=datetime.now(),
            end_time=None,
            current_step_id=current_step_id
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        logger.info(
            f"用户 {current_user.username} 首次开始实验 {experiment.title}，创建新记录: {new_record.id}，当前步骤ID为: {new_record.current_step_id}")
        response_data = new_record.to_dict()

    # 无论哪种情况，都将当前步骤的正确答案和解释填充到响应中
    # 这是一个关键点：这里填充的是当前 step 的**正确答案**和**解释**，而不是用户之前的答案。
    response_data['answers'] = target_step.answer  # 将正确答案填充到 'answers' 字段
    response_data['explanation'] = target_step.explanation  # 将正确解释填充到 'explanation' 字段
    return response_data


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
    获取当前用户在指定实验下的**最新**实验记录详情，包括每个步骤在数据库中记录的状态和分数。
    不包含用户提交的具体答案。
    如果记录不存在，则返回一个初始化的记录（status='not_started'）。
    每个步骤的状态直接根据数据库中该步骤的实际状态设定。
    包含详细调试日志。
    """
    logger.debug(f"进入 get_experiment_record_details，实验ID: {experiment_id}, 用户ID: {current_user.id}")

    experiment = db.query(Experiment).options(joinedload(Experiment.steps)).filter(
        Experiment.id == experiment_id).first()
    if not experiment:
        logger.warning(f"实验 {experiment_id} 不存在。")
        raise HTTPException(status_code=404, detail="实验不存在")

    record = db.query(ExperimentRecord).filter_by(
        user_id=current_user.id,
        experiment_id=experiment_id
    ).order_by(desc(ExperimentRecord.start_time)).first()

    all_steps = sorted(experiment.steps, key=lambda s: s.id)
    logger.debug(f"实验 {experiment_id} 共有 {len(all_steps)} 个步骤。")

    if not record:
        logger.info(f"用户 {current_user.username} 在实验 {experiment_id} 没有现有记录，返回默认未开始状态。")

        steps_status_list = []
        for step in all_steps:
            steps_status_list.append(ExperimentStepStatus(
                id=step.id,
                step_number=step.id,
                question=step.question,
                image_path=step.image_path,
                image_description=step.image_description,
                options=json.loads(step.options) if step.options and isinstance(step.options, str) else step.options,
                status="pending",
                score=0.0,
                user_answer=None
            ))
            logger.debug(f"步骤 {step.id}: 无记录，设置为 status=pending, score=0.0, user_answer=None")

        return ExperimentRecordDetails(
            id=-1,
            user_id=current_user.id,
            experiment_id=experiment_id,
            status=ExperimentStatus.NOT_STARTED,
            score=0.0,
            start_time=datetime.min,
            end_time=None,
            steps_status=steps_status_list
        )

    logger.info(
        f"用户 {current_user.username} 在实验 {experiment_id} 找到最新记录: ID={record.id}, 整体状态={record.status.value}, 当前步骤ID={record.current_step_id}")

    steps_status_list = []

    for step in all_steps:
        logger.debug(f"\n--- 处理步骤 {step.id} ---")
        step_status: str = "pending"
        step_score: float = 0.0

        if record.current_step_id is not None and step.id == record.current_step_id:
            if record.status == ExperimentStatus.IN_PROGRESS:
                step_status = "answering"
                # 在进行中状态下，单个步骤的分数暂时为 0.0，因为总分还未确定
                step_score = 0.0
                logger.debug(
                    f"步骤 {step.id}: 匹配 record.current_step_id 且 record.status 为 IN_PROGRESS，设置为 answering, score=0.0。")
            elif record.status == ExperimentStatus.COMPLETED:
                step_status = "completed"
                # 当整体实验记录为 COMPLETED 时，我们将该步骤的分数设置为 record 的总分数
                step_score = record.score
                logger.debug(
                    f"步骤 {step.id}: 匹配 record.current_step_id 且 record.status 为 COMPLETED，设置为 completed, score={step_score}。")
            else:
                step_status = "pending"
                step_score = 0.0
                logger.debug(
                    f"步骤 {step.id}: 匹配 record.current_step_id 但 record.status 为 {record.status.value}，设置为 pending, score=0.0。")
        else:
            # 如果当前步骤ID不包括 record.current_step_id，且实验已完成，则该步骤也视为已完成
            if record.status == ExperimentStatus.COMPLETED:
                step_status = "completed"
                step_score = record.score  # 此时，所有步骤的分数都显示为实验总分
            else:
                step_status = "pending"
                step_score = 0.0
            logger.debug(
                f"步骤 {step.id}: 不匹配 record.current_step_id ({record.current_step_id if record.current_step_id else 'None'})，设置为 {step_status}, score={step_score}。")

        steps_status_list.append(ExperimentStepStatus(
            id=step.id,
            step_number=step.id,
            question=step.question,
            image_path=step.image_path,
            image_description=step.image_description,
            options=json.loads(step.options) if step.options and isinstance(step.options, str) else step.options,
            status=step_status,
            score=step_score,
            user_answer=None
        ))
        logger.debug(f"步骤 {step.id} 最终输出 (不含答案): status='{step_status}', score={step_score}")

    logger.info(f"用户 {current_user.username} 获取实验 {experiment_id} 的最新记录详情成功，记录ID: {record.id}")
    return ExperimentRecordDetails(
        id=record.id,
        user_id=record.user_id,
        experiment_id=record.experiment_id,
        status=record.status,
        score=record.score,
        start_time=record.start_time,
        end_time=record.end_time,
        steps_status=steps_status_list
    )


@exp_router.post("/records/complete", status_code=status.HTTP_200_OK)
async def complete_experiment_record(
        record_data: ExperimentRecordComplete,
        current_user: User = Depends(get_required_user),
        db: Session = Depends(get_db)
):
    """
    标记一个用户实验记录为已完成，并更新最终得分和结束时间。
    前端传入 user_id, experiment_id, score, 和可选的 current_step_id。
    """
    logger.info(f"用户 {current_user.username} 请求完成实验记录，数据: {record_data.model_dump()}")

    if record_data.user_id != current_user.id:
        logger.warning(f"用户 {current_user.username} 尝试修改其他用户 ({record_data.user_id}) 的实验记录。")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此实验记录，只能操作自己的记录。"
        )

    record = db.query(ExperimentRecord).filter(
        ExperimentRecord.user_id == record_data.user_id,
        ExperimentRecord.experiment_id == record_data.experiment_id
    ).order_by(desc(ExperimentRecord.start_time)).first()

    if not record:
        logger.error(f"未找到用户 {record_data.user_id} 在实验 {record_data.experiment_id} 下的进行中或未开始的记录。")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到对应实验记录或记录已完成。请确保该实验有未开始或进行中的记录。"
        )

    if record.status == ExperimentStatus.COMPLETED:
        logger.warning(f"用户 {current_user.username} 尝试重复完成已完成的实验记录 {record.id}。")
        return {"message": "实验记录已是完成状态，无需重复操作。", "record": record.to_dict()}

    record.status = ExperimentStatus.COMPLETED
    record.score = record_data.score
    record.end_time = datetime.now()

    if record_data.current_step_id is not None:
        step_exists = db.query(ExperimentStep).filter(
            ExperimentStep.id == record_data.current_step_id,
            ExperimentStep.experiment_id == record_data.experiment_id
        ).first()
        if not step_exists:
            logger.warning(
                f"用户 {current_user.username} 提交的 current_step_id {record_data.current_step_id} 无效或不属于实验 {record_data.experiment_id}。将忽略此字段。")
            pass
        else:
            record.current_step_id = record_data.current_step_id

    try:
        db.commit()
        db.refresh(record)
        logger.info(f"用户 {current_user.username} 成功完成实验记录 {record.id}，得分: {record.score}")
        return {"message": "实验记录已成功更新为完成状态。", "record": record.to_dict()}
    except Exception as e:
        db.rollback()
        logger.error(f"保存实验记录 {record.id} 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存实验记录时发生服务器错误: {e}"
        )