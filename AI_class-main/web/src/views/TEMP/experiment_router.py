import json
from datetime import datetime
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session
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
    rating: int = Field(..., ge=1, le=5)  # 评分在1-5之间
    comment: str
    aspect_ratings: Optional[Dict[str, int]] = None


class AnswersSubmit(BaseModel):
    answers: Dict[int, str]  # {step_id: user_answer}


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

    # 检查用户是否已订阅此课程
    if course in user.subscribed_courses: # 通过 relationship 检查
        raise HTTPException(status_code=400, detail="用户已订阅此课程")

    # 添加课程到用户的 subscribed_courses 列表中，SQLA 会自动处理关联表
    user.subscribed_courses.append(course)
    db.commit()
    logger.info(f"管理员 {current_user.username} 为用户 {user.username} 分配了课程 {course.title}")
    return {"message": "课程分配成功"}

# ==================== 普通用户操作接口 ====================
@exp_router.get("/courses") # 修改路径，使其更通用
async def get_all_courses(
        current_user: User = Depends(get_required_user), # 仍然需要登录用户，以便知道是谁在请求
        db: Session = Depends(get_db)
):
    """获取所有可用的课程列表，无论用户是否订阅"""
    try:
        courses = db.query(Course).all() # 查询所有课程
        return [course.to_dict() for course in courses]
    except Exception as e:
        logger.error(f"用户 {current_user.username} 获取所有课程列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取课程列表失败")
#
@exp_router.get("/course/{course_id}/experiments")
async def get_experiments_in_course(
        course_id: int,
        current_user: User = Depends(get_required_user), # 仍然需要登录用户，但不再强制订阅
        db: Session = Depends(get_db)
):
    """获取指定课程下的所有实验卡片列表"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    # 所有登录用户都可以访问
    # if course not in current_user.subscribed_courses:
    #     raise HTTPException(status_code=403, detail="您无权访问此课程下的实验")

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

    # 手动构建嵌套的字典响应
    response_dict = experiment.to_dict()

    # 包含实验步骤 (不含答案)
    response_dict["curriculum"] = [step.to_dict(include_answer=False) for step in experiment.steps]

    # 包含评论
    reviews = db.query(Review).filter(Review.experiment_id == experiment_id).order_by(Review.timestamp.desc()).all()
    response_dict["reviews"] = [review.to_dict() for review in reviews]

    # 计算平均分
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

    # 可选：检查用户是否已完成实验才能评论
    # record = db.query(ExperimentRecord).filter_by(user_id=current_user.id, experiment_id=experiment_id, status=ExperimentStatus.COMPLETED).first()
    # if not record:
    #     raise HTTPException(status_code=403, detail="请先完成实验再进行评论")

    new_review = Review(
        **review_data.model_dump(),
        user_id=current_user.id,
        experiment_id=experiment_id
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review.to_dict()


@exp_router.post("/{experiment_id}/start")
async def start_experiment(
        experiment_id: int,
        current_user: User = Depends(get_required_user),
        db: Session = Depends(get_db)
):
    """开始或继续一个实验，返回实验记录信息"""
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")

    # 查找是否已经有正在进行的记录
    record = db.query(ExperimentRecord).filter_by(
        user_id=current_user.id,
        experiment_id=experiment_id,
        status=ExperimentStatus.IN_PROGRESS
    ).first()

    if record:
        logger.info(f"用户 {current_user.username} 继续实验 {experiment.title}")
        return record.to_dict()

    # 创建一条新记录
    new_record = ExperimentRecord(
        user_id=current_user.id,
        experiment_id=experiment_id,
        status=ExperimentStatus.IN_PROGRESS
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    logger.info(f"用户 {current_user.username} 开始新实验 {experiment.title}")
    return new_record.to_dict()


@exp_router.post("/records/{record_id}/submit")
async def submit_experiment_answers(
        record_id: int,
        submission: AnswersSubmit,
        current_user: User = Depends(get_required_user),
        db: Session = Depends(get_db)
):
    """提交整个实验的答案并获取评分"""
    record = db.query(ExperimentRecord).filter(ExperimentRecord.id == record_id).first()

    # 关键的所有权和状态验证
    if not record:
        raise HTTPException(status_code=404, detail="实验记录不存在")
    if record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此实验记录")
    if record.status != ExperimentStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="此实验不是正在进行的状态，无法提交")

    # 获取正确答案
    steps = record.experiment.steps
    correct_answers = {step.id: step.answer for step in steps}

    # 计算分数
    score = 0
    total_questions = len(steps)
    user_answers = submission.answers

    for step_id, correct_answer in correct_answers.items():
        user_answer = user_answers.get(step_id)
        if user_answer and str(user_answer) == str(correct_answer):
            score += 1

    final_score = (score / total_questions) * 100 if total_questions > 0 else 0

    # 更新记录
    record.score = final_score
    record.status = ExperimentStatus.COMPLETED
    record.answers = user_answers
    record.end_time = datetime.now()
    db.commit()

    logger.info(f"用户 {current_user.username} 完成实验 {record.experiment.title}，得分: {final_score}")

    return record.to_dict()