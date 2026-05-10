"""
Celery 应用配置
"""

from celery import Celery
from backend.config import config

celery_app = Celery(
    "novel_writer",
    broker=config.REDIS_URL,
    backend=config.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,       # 单任务最大执行 1 小时
    task_soft_time_limit=3000,  # 软超时 50 分钟
    worker_max_tasks_per_child=50,
    worker_prefetch_multiplier=1,
)

# 导入任务模块
import backend.tasks.analyze_task  # noqa
import backend.tasks.write_task  # noqa
import backend.tasks.publish_task  # noqa
