"""
今日头条自动发布系统 - 定时调度器
长期后台运行，按设定时间自动执行发布任务
用法：python scheduler.py
"""

import schedule
import time
import logging
import sys
import os

# 切换工作目录到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import SCHEDULE_HOURS, LOG_FILE
from main import run, setup_logging


def scheduled_task():
    """定时任务执行函数"""
    logger = logging.getLogger("scheduler")
    logger.info(f"定时任务触发，开始执行...")
    try:
        run(dry_run=False)
    except Exception as e:
        logger.error(f"定时任务执行异常: {e}", exc_info=True)


def main():
    setup_logging()
    logger = logging.getLogger("scheduler")
    
    logger.info("定时调度器启动")
    logger.info(f"每天执行时间: {[f'{h:02d}:00' for h in SCHEDULE_HOURS]}")
    
    # 注册定时任务
    for hour in SCHEDULE_HOURS:
        schedule.every().day.at(f"{hour:02d}:00").do(scheduled_task)
        logger.info(f"已注册定时任务: 每天 {hour:02d}:00")
    
    print(f"\n调度器运行中，每天在 {[f'{h}:00' for h in SCHEDULE_HOURS]} 自动发布")
    print("按 Ctrl+C 停止\n")
    
    # 启动时立即执行一次（可选，注释掉则仅按计划时间运行）
    # scheduled_task()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)  # 每30秒检查一次
        except KeyboardInterrupt:
            logger.info("收到停止信号，调度器退出")
            print("\n调度器已停止")
            sys.exit(0)
        except Exception as e:
            logger.error(f"调度循环异常: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
