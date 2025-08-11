#!/usr/bin/env python3
"""
為現有實驗添加 type 字段的腳本
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from server.models import Base
from server.models.experiment_model import Experiment
from server.models.user_model import User

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../saves/data/server.db'))
DB_URL = f'sqlite:///{DB_PATH}'

def add_experiment_type_column():
    """為 experiments 表添加 type 字段"""
    engine = create_engine(DB_URL)
    # SQLite 沒有 information_schema，直接嘗試添加（如果已存在會報錯，忽略即可）
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE experiments ADD COLUMN type VARCHAR(20) DEFAULT 'A'"))
            print("成功添加 type 字段")
        except Exception as e:
            if 'duplicate column name' in str(e) or 'already exists' in str(e):
                print("type 字段已存在，跳過添加")
            else:
                print(f"添加 type 字段時出錯: {e}")

def update_existing_experiments():
    """更新現有實驗的 type 字段"""
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        experiments = session.query(Experiment).all()
        for i, experiment in enumerate(experiments):
            if i == 0:
                experiment.type = 'A'
            elif i == 1:
                experiment.type = 'B'
            else:
                experiment.type = 'A'
            print(f"更新實驗 {experiment.id} ({experiment.title}) 的類型為: {experiment.type}")
        session.commit()
        print(f"成功更新 {len(experiments)} 個實驗的類型")
    except Exception as e:
        print(f"更新實驗類型時出錯: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    print("開始為實驗添加類型字段...")
    add_experiment_type_column()
    update_existing_experiments()
    print("完成！")

if __name__ == "__main__":
    main() 