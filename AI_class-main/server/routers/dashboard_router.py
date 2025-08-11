from datetime import datetime, timedelta, date, timezone
from typing import List
import pytz # 为了更精确的时区处理，虽然在这里主要用于 timedelta，但保持引入以防后续扩展

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, cast, Date, text
from sqlalchemy.orm import Session
from sqlalchemy.sql import case

# 模仿您的导入结构
from server.utils.auth_middleware import get_admin_user, get_db
from server.models.user_model import User, OperationLog
from src.utils.logging_config import logger

# --- 创建新的路由器 ---
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# 定义你的本地时区（如果需要将日期时间对象转换为带时区信息，但在这里主要用 timedelta）
# LOCAL_TIMEZONE = pytz.timezone('Asia/Shanghai') # 如果需要将原始datetime对象附加上时区信息，会用到

# --- Pydantic 模型定义 ---
class DailyActivityStat(BaseModel):
    date: str
    total_operations: int
    registration_count: int


# --- API 路由 ---
@dashboard_router.get(
    "/activity-stats",
    response_model=List[DailyActivityStat],
    summary="获取最近14天的操作日志统计"
)
async def get_activity_stats(
        current_user: User = Depends(get_admin_user),
        db: Session = Depends(get_db)
):
    try:
        logger.info(f"管理员 {current_user.username} 请求获取活动日志统计。")

        # --- 查询 OperationLog 表的总行数 ---
        total_rows_in_table = db.query(func.count(OperationLog.id)).scalar()
        logger.debug(f"OperationLog 表的总行数: {total_rows_in_table}")

        if total_rows_in_table == 0:
            logger.error("OperationLog 表中没有数据，请检查数据库连接或表数据是否为空。")
            raise HTTPException(status_code=404, detail="服务器活动日志数据为空，无法提供统计。")

        # --- 打印当前时间和时区信息 ---
        now_local = datetime.now()
        now_utc = datetime.utcnow()
        logger.debug(f"当前Python本地时间: {now_local}")
        logger.debug(f"当前Python UTC时间: {now_utc}")
        logger.debug(f"当前Python本地时区: {now_local.astimezone().tzinfo}")


        # 1. 直接从数据库获取所有 OperationLog 记录
        # 注意：如果 OperationLog 表非常大，这种做法效率很低，但符合你要求“不用WHERE过滤”
        all_logs = db.query(OperationLog).all()
        logger.debug(f"直接从数据库获取所有 OperationLog 记录数: {len(all_logs)}")

        # 2. 手动在 Python 内存中进行时间偏移和聚合
        daily_stats_local = {} # 存储按本地日期聚合的数据

        # 获取本地的今天和14天前的日期，用于最终过滤和补全
        today_local_date = date.today()
        start_date_local_filter = today_local_date - timedelta(days=13) # 14天前

        for log in all_logs:
            if not log.timestamp:
                logger.warning(f"OperationLog ID {log.id} 有空 timestamp，跳过。")
                continue

            # 关键：将 UTC 时间戳加上 8 小时，模拟转换为本地时间
            # 假设数据库返回的 timestamp 是 naive datetime (不带时区信息) 且代表 UTC 时间
            # 或者已经是带 UTC 时区的 datetime 对象，加上 timedelta 也是安全的
            local_time_adjusted_dt = log.timestamp + timedelta(hours=8)

            # 获取调整后的本地日期
            local_date_for_log = local_time_adjusted_dt.date()
            local_date_str = local_date_for_log.isoformat()

            # 仅统计落在最近 14 天本地日期范围内的记录
            if start_date_local_filter <= local_date_for_log <= today_local_date:
                if local_date_str not in daily_stats_local:
                    daily_stats_local[local_date_str] = {
                        'total_operations': 0,
                        'registration_count': 0
                    }

                daily_stats_local[local_date_str]['total_operations'] += 1
                if log.operation == '用户注册':
                    daily_stats_local[local_date_str]['registration_count'] += 1
                elif log.operation and '用户注册' in log.operation:
                    # 仅作调试用途，不计入实际注册数，除非用户明确要求模糊匹配
                    logger.debug(f"发现模糊匹配 '用户注册' 的操作: ID={log.id}, Operation='{log.operation}'")


        logger.debug(f"Python 内存中按本地日期聚合后的结果: {daily_stats_local}")
        logger.debug(f"Python 内存中聚合到的本地天数: {len(daily_stats_local)}")

        # 3. 将聚合结果转换为 DailyActivityStat 列表，并补全缺失的日期
        final_stats = []
        for i in range(14):
            current_date_to_add = start_date_local_filter + timedelta(days=i)
            current_date_str = current_date_to_add.isoformat()

            if current_date_str in daily_stats_local:
                stats_for_date = daily_stats_local[current_date_str]
                final_stats.append(DailyActivityStat(
                    date=current_date_str,
                    total_operations=stats_for_date['total_operations'],
                    registration_count=stats_for_date['registration_count']
                ))
            else:
                # 补全没有数据的日期
                final_stats.append(DailyActivityStat(
                    date=current_date_str,
                    total_operations=0,
                    registration_count=0
                ))

        return final_stats

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取活动日志统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取服务器活动数据时发生内部错误。")