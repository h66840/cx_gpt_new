import hashlib
import os # 需要导入 os 模块来生成随机盐
import sys
from datetime import datetime

# 假设你的项目根目录包含 src 和 server 目录
# 将项目根目录添加到 Python 路径，以便正确导入
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# 从你的 db_manager 文件中导入 DBManager 实例
import os
import pathlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from src import config
from server.models import Base
from server.models.user_model import User
from server.models.kb_models import KnowledgeDatabase, KnowledgeFile, KnowledgeNode
from src.utils import logger

class DBManager:
    """数据库管理器 - 只提供基础的数据库连接和会话管理"""

    def __init__(self):
        """初始化数据库管理器"""
        self.db_path = os.path.join(config.save_dir, "data", "server.db")
        self.ensure_db_dir()

        # 创建SQLAlchemy引擎
        self.engine = create_engine(f"sqlite:///{self.db_path}")

        # 创建会话工厂
        self.Session = sessionmaker(bind=self.engine)

        # 确保表存在
        self.create_tables()

    def ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        pathlib.Path(db_dir).mkdir(parents=True, exist_ok=True)

    def create_tables(self):
        """创建数据库表"""
        # 确保所有表都会被创建
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created/checked")

    def get_session(self):
        """获取数据库会话"""
        return self.Session()

    @contextmanager
    def get_session_context(self):
        """获取数据库会话的上下文管理器"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            session.close()

    def check_first_run(self):
        """检查是否首次运行"""
        session = self.get_session()
        try:
            # 检查是否有任何用户存在
            return session.query(User).count() == 0
        finally:
            session.close()

# 创建全局数据库管理器实例
db_manager = DBManager()
# 替换为实际的 db_manager 导入路径
from server.models.user_model import User # 确保 User 模型可以被正确导入

# --- 1. 使用与 AuthUtils 完全一致的密码哈希函数 ---
# 注意：这个函数必须与你 AuthUtils.py 中的 hash_password 完全一致
def hash_password_with_salt(password: str) -> str:
    """
    使用 SHA-256 哈希密码，并添加盐值。
    此函数与 AuthUtils.hash_password 的逻辑保持一致。
    """
    # 生成盐
    salt = os.urandom(32).hex()
    # 哈希密码
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    # 返回格式: "哈希值:盐"
    return f"{hashed}:{salt}"

# --- 2. 动态生成并添加用户数据 ---
def add_test_users(num_users: int = 100, start_id: int = 15):
    """
    向数据库添加指定数量的测试用户。
    使用与 AuthUtils 一致的加盐哈希逻辑。
    """
    try:
        with db_manager.get_session_context() as session:
            print(f"正在添加 {num_users} 个测试用户，用户名和密码从 {start_id} 开始...")
            added_count = 0
            for i in range(num_users):
                user_number = start_id + i
                username = f"{user_number}"
                password = str(user_number) # 密码也设置为对应的数字字符串

                # 使用与 AuthUtils 相同的加盐哈希函数
                hashed_password = hash_password_with_salt(password)

                # 检查用户是否已存在
                existing_user = session.query(User).filter(User.username == username).first()
                if existing_user:
                    print(f"用户 '{username}' 已存在，跳过。")
                    continue

                new_user = User(
                    username=username,
                    password_hash=hashed_password, # 存储加盐哈希值
                    role='user',
                    organization=f"Org-{user_number % 10}"
                )
                session.add(new_user)
                added_count += 1
                if (i + 1) % 10 == 0:
                    print(f"  已添加 {added_count} 个用户到会话...")

            print(f"成功将 {added_count} 个用户添加到数据库会话，即将提交。")
            print(f"所有用户添加完成，总计 {added_count} 个新用户已保存。")

    except Exception as e:
        print(f"添加用户时发生错误: {e}")

# --- 3. 执行添加操作 ---
if __name__ == "__main__":
    # 在运行前，请确保这里的导入路径与您的项目结构相匹配
    # 例如：from my_project.db_manager import db_manager

    # 首先删除旧的测试用户（可选，但推荐，以确保数据干净）
    print("正在清理旧的测试用户数据...")
    with db_manager.get_session_context() as session:
        # 删除所有 username 以 "user" 开头且后面是数字的用户
        users_to_delete = session.query(User).filter(User.username.like("user%")).all()
        for user in users_to_delete:
            session.delete(user)
        session.commit()
    print("旧的测试用户数据清理完成。")

    # 运行添加用户函数
    add_test_users(num_users=100, start_id=15)

    # 验证数据 (可选)
    with db_manager.get_session_context() as session:
        total_users = session.query(User).count()
        print(f"\n数据库中当前总用户数: {total_users}")
        user_15 = session.query(User).filter_by(username="user15").first()
        if user_15:
            print(f"找到用户 user15: ID={user_15.id}, 密码哈希={user_15.password_hash}")
        user_114 = session.query(User).filter_by(username="user114").first()
        if user_114:
            print(f"找到用户 user114: ID={user_114.id}, 密码哈希={user_114.password_hash}")