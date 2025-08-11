# server/models/experiment_model.py

import enum
from sqlalchemy import (Column, Integer, String, Float, ForeignKey, DateTime,
                        Enum, Text, JSON, Table)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # 导入 func


from server.models import Base

# --- 关联表定义 ---
# 用户和课程的多对多关联表
# 包含两个外键字段：user_id 和 course_id，共同组成复合主键
user_course_association_table = Table('user_course_link', Base.metadata,
                                      Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
                                      Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True)
                                      )


# --- 枚举定义 ---
class ExperimentStatus(enum.Enum):
    """
    实验状态枚举类
    定义实验的三种状态：
    - NOT_STARTED: 未开始
    - IN_PROGRESS: 进行中
    - COMPLETED: 已完成
    """
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# --- 核心模型 ---

class Course(Base):
    """
    课程数据模型

    属性:
        id (int): 课程唯一标识符，主键
        title (str): 课程标题，非空且唯一
        description (str): 课程描述
        image (str): 课程封面图片路径

    关系:
        subscribers: 订阅该课程的用户列表（多对多关系）
        experiments: 该课程下的实验列表（一对多关系）
    """
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    image = Column(String(255))

    # 通过 secondary 参数指定多对多关系的关联表
    subscribers = relationship(
        "User",
        secondary=user_course_association_table,
        back_populates="subscribed_courses"
    )

    experiments = relationship("Experiment", back_populates="course", cascade="all, delete-orphan")

    def to_dict(self):
        """
        将课程对象转换为字典格式

        返回:
            dict: 包含课程基本信息的字典
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "image": self.image
        }


class Experiment(Base):
    """
    实验数据模型

    属性:
        id (int): 实验唯一标识符，主键
        title (str): 实验标题，非空
        description (str): 实验详细描述
        tag (str): 实验标签
        image (str): 实验封面图片路径
        type (str): 实验类型，用于区分不同的展示界面
        course_id (int): 所属课程的外键

    关系:
        course: 所属课程对象（多对一关系）
        steps: 实验步骤列表（一对多关系）
        reviews: 实验评论列表（一对多关系）
    """
    __tablename__ = 'experiments'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    tag = Column(String(50))
    image = Column(String(255))
    type = Column(String(20), default='A')  # 新增类型字段，默认为A

    course_id = Column(Integer, ForeignKey('courses.id'))

    # 关联关系
    course = relationship("Course", back_populates="experiments")
    steps = relationship("ExperimentStep", back_populates="experiment", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="experiment", cascade="all, delete-orphan")

    def to_dict(self):
        """
        将实验对象转换为字典格式

        返回:
            dict: 包含实验基本信息的字典
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tag": self.tag,
            "image": self.image,
            "type": self.type,  # 添加类型字段
            "course_id": self.course_id
        }


class ExperimentStep(Base):
    """
    实验步骤数据模型

    属性:
        id (int): 步骤唯一标识符，主键
        question (str): 步骤问题，非空
        options (dict): 选项列表（JSON格式）
        answer (str): 正确答案，非空
        explanation (str): 答案解析
        image_path (str): 步骤相关图片路径
        image_description (str): 图片描述
        experiment_id (int): 所属实验的外键

    关系:
        experiment: 所属实验对象（多对一关系）
    """
    __tablename__ = 'experiment_steps'

    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    options = Column(JSON) # 保持 JSON 类型，因为你没有要求修改
    answer = Column(Text, nullable=False)
    explanation = Column(Text)
    image_path = Column(String(255))
    image_description = Column(String(500))

    experiment_id = Column(Integer, ForeignKey('experiments.id'))

    # 关联关系
    experiment = relationship("Experiment", back_populates="steps")

    def to_dict(self, include_answer=False):
        """
        将实验步骤对象转换为字典格式

        参数:
            include_answer (bool): 是否包含答案信息

        返回:
            dict: 包含步骤信息的字典，根据参数决定是否包含答案
        """
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
    """
    实验评论数据模型

    属性:
        id (int): 评论唯一标识符，主键
        rating (int): 评分
        comment (str): 评论内容
        aspect_ratings (dict): 各方面评分（JSON格式）
        timestamp (datetime): 评论时间，默认为当前时间
        user_id (int): 评论用户的外键
        experiment_id (int): 所属实验的外键

    关系:
        user: 评论用户对象（多对一关系）
        experiment: 所属实验对象（多对一关系）
    """
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    rating = Column(Integer)
    comment = Column(Text)
    aspect_ratings = Column(JSON)
    # 修改点：参照 User 模型的时间处理方式
    timestamp = Column(DateTime, default=func.now())

    user_id = Column(Integer, ForeignKey('users.id'))
    experiment_id = Column(Integer, ForeignKey('experiments.id'))

    # 关联关系
    user = relationship("User")
    experiment = relationship("Experiment", back_populates="reviews")

    def to_dict(self):
        """
        将评论对象转换为字典格式

        返回:
            dict: 包含评论信息的字典，包含用户名称等扩展信息
        """
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
    """
    用户实验单个步骤记录数据模型

    属性:
        id (int): 记录唯一标识符，主键
        status (ExperimentStatus): 步骤状态，默认为未开始
        score (float): 实验步骤得分，默认为0.0
        answers (str): 用户答案记录（字符串类型，不再是JSON）
        start_time (datetime): 开始时间，默认为当前时间
        end_time (datetime): 结束时间
        user_id (int): 用户外键
        experiment_id (int): 实验外键
        current_step_id (int): 当前进行到的实验步骤ID (新增)

    关系:
        user: 用户对象（多对一关系）
        experiment: 实验对象（多对一关系）
        current_step: 当前进行到的实验步骤对象（多对一关系） (新增)
    """
    __tablename__ = 'experiment_records'

    id = Column(Integer, primary_key=True)
    status = Column(Enum(ExperimentStatus), nullable=False, default=ExperimentStatus.NOT_STARTED)
    score = Column(Float, default=0.0)

    answers = Column(Text, nullable=True)  # 现在存储纯字符串答案，允许为NULL
    # 修改点：参照 User 模型的时间处理方式
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)

    user_id = Column(Integer, ForeignKey('users.id'))
    experiment_id = Column(Integer, ForeignKey('experiments.id'))
    # 新增的外键字段，关联 ExperimentStep 的 id
    current_step_id = Column(Integer, ForeignKey('experiment_steps.id'), nullable=True)

    # 关联关系
    user = relationship("User")
    experiment = relationship("Experiment")
    # 新增的关联关系
    current_step = relationship("ExperimentStep")


    def to_dict(self):
        """
        将实验记录对象转换为字典格式

        返回:
            dict: 包含实验记录信息的字典，包含时间戳的ISO格式字符串
        """
        return {
            "id": self.id,
            "status": self.status.value,
            "score": self.score,
            "answers": self.answers, # answers 现在是字符串
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "user_id": self.user_id,
            "experiment_id": self.experiment_id,
            "current_step_id": self.current_step_id  # 在字典中也包含新字段
        }