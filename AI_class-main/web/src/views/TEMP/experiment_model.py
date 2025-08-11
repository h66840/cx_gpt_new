# server/models/experiment_model.py

import enum
from sqlalchemy import (Column, Integer, String, Float, ForeignKey, DateTime,
                        Enum, Text, JSON, Table)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from server.models import Base


# --- 关联表定义 ---
user_course_association_table = Table('user_course_link', Base.metadata,
                                      Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
                                      Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True)
                                      )


# --- 枚举定义 ---
class ExperimentStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# --- 核心模型 ---

class Course(Base):
    """课程模型"""
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))

    # 通过 secondary 参数指定多对多关系的关联表
    subscribers = relationship(
        "User",
        secondary=user_course_association_table,
        back_populates="subscribed_courses"
    )

    experiments = relationship("Experiment", back_populates="course", cascade="all, delete-orphan")

    def to_dict(self):
        """将课程对象转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description
        }


class Experiment(Base):
    """实验整体模型"""
    __tablename__ = 'experiments'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    tag = Column(String(50))
    image = Column(String(255))

    course_id = Column(Integer, ForeignKey('courses.id'))

    # 关联关系
    course = relationship("Course", back_populates="experiments")
    steps = relationship("ExperimentStep", back_populates="experiment", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="experiment", cascade="all, delete-orphan")

    def to_dict(self):
        """将实验对象转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tag": self.tag,
            "image": self.image,
            "course_id": self.course_id
        }


class ExperimentStep(Base):
    """实验步骤模型"""
    __tablename__ = 'experiment_steps'

    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    options = Column(JSON)
    answer = Column(Text, nullable=False)
    explanation = Column(Text)
    image_path = Column(String(255))
    image_description = Column(String(500))

    experiment_id = Column(Integer, ForeignKey('experiments.id'))

    # 关联关系
    experiment = relationship("Experiment", back_populates="steps")

    def to_dict(self, include_answer=False):
        """将实验步骤对象转换为字典，可选择是否包含答案"""
        result = {
            "id": self.id,
            "question": self.question,
            "options": self.options,
            "explanation": self.explanation,
            "image_path": self.image_path,
            "image_description": self.image_description,
            "experiment_id": self.experiment_id
        }
        if include_answer:
            result["answer"] = self.answer
        return result


class Review(Base):
    """评论模型"""
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    rating = Column(Integer)
    comment = Column(Text)
    aspect_ratings = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey('users.id'))
    experiment_id = Column(Integer, ForeignKey('experiments.id'))

    # 关联关系
    user = relationship("User")
    experiment = relationship("Experiment", back_populates="reviews")

    def to_dict(self):
        """将评论对象转换为字典"""
        return {
            "id": self.id,
            "rating": self.rating,
            "comment": self.comment,
            "aspect_ratings": self.aspect_ratings,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "user_name": self.user.username if self.user else "未知用户",
            "experiment_id": self.experiment_id
        }


class ExperimentRecord(Base):
    """用户实验记录模型"""
    __tablename__ = 'experiment_records'

    id = Column(Integer, primary_key=True)
    status = Column(Enum(ExperimentStatus), nullable=False, default=ExperimentStatus.NOT_STARTED)
    score = Column(Float, default=0.0)
    answers = Column(JSON)  # 存储 {step_id: user_answer}
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)

    user_id = Column(Integer, ForeignKey('users.id'))
    experiment_id = Column(Integer, ForeignKey('experiments.id'))

    # 关联关系
    user = relationship("User")
    experiment = relationship("Experiment")

    def to_dict(self):
        """将实验记录对象转换为字典"""
        return {
            "id": self.id,
            "status": self.status.value,
            "score": self.score,
            "answers": self.answers,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "user_id": self.user_id,
            "experiment_id": self.experiment_id
        }