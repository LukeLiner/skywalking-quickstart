# -*- coding: utf-8 -*-
"""
定时任务调度器 - 自动从SkyWalking获取资源并导入Neo4j
"""

import schedule
import time


def job():
    """定时执行的数据同步任务"""
    import io
    import sys
    
    # 每次执行时重新设置stdout，避免文件关闭问题
    if sys.stdout.closed:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', mode='w')
    
    print("\n" + "="*60)
    print("Execute scheduled sync task")
    print("="*60)
    try:
        from import_from_skywalking import main as sync_data
        sync_data()
        print("\nSync completed successfully")
    except Exception as e:
        print(f"\nSync failed: {e}")


def main():
    """主函数 - 启动定时任务"""
    print("""
============================================================
Scheduled Resource Sync Service
============================================================

Function: Sync resources from SkyWalking OAP to Neo4j
Data source: SkyWalking OAP (dynamic)

Usage: python scheduler.py [interval_minutes]

Examples:
  python scheduler.py       # every 5 minutes
  python scheduler.py 10    # every 10 minutes
  python scheduler.py 1     # every 1 minute (test)

Stop: Ctrl+C
============================================================
    """)
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('interval', type=int, nargs='?', default=5, help='sync interval (minutes)')
    args = parser.parse_args()
    
    interval_minutes = args.interval
    
    schedule.every(interval_minutes).minutes.do(job)
    
    print(f"\nScheduler started, running every {interval_minutes} minutes")
    print("First run will start now...\n")
    
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
