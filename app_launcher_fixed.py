#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
北斗卫星状态监控系统启动器 (修复版)
自动启动Web服务并打开浏览器
"""

import os
import sys
import time
import threading
import webbrowser
import subprocess
from pathlib import Path

# 强制导入所有可能需要的模块，确保PyInstaller包含它们
try:
    import flask
    import flask_cors
    import oracledb
    import oracledb.defaults
    import oracledb.exceptions
    import oracledb.pool
    import oracledb.connection
    import oracledb.cursor
    import concurrent.futures
    import json
    import logging
    print("✅ 所有模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    input("按回车键退出...")
    sys.exit(1)

# 导入主程序
try:
    from oracle_concurrent_executor import app, init_database, logger
    print("✅ 主程序模块导入成功")
except ImportError as e:
    print(f"❌ 主程序导入失败: {e}")
    print("请确保 oracle_concurrent_executor.py 文件存在且配置正确")
    input("按回车键退出...")
    sys.exit(1)

def open_browser(url, delay=2):
    """延迟打开浏览器"""
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            logger.info(f"已自动打开浏览器: {url}")
        except Exception as e:
            logger.error(f"打开浏览器失败: {e}")
            print(f"请手动在浏览器中打开: {url}")
    
    thread = threading.Thread(target=_open)
    thread.daemon = True
    thread.start()

def main():
    """主启动函数"""
    print("=" * 60)
    print("           北斗卫星状态监控系统")
    print("=" * 60)
    print()
    
    # 检查资源文件
    current_dir = Path(__file__).parent
    index_file = current_dir / "index.html"
    
    if not index_file.exists():
        print("❌ 错误: 找不到 index.html 文件")
        print(f"请确保 {index_file} 文件存在")
        input("按回车键退出...")
        return
    
    print("✅ 检查资源文件完成")
    
    # 初始化数据库连接
    print("🔄 正在初始化数据库连接...")
    if not init_database():
        print("❌ 数据库连接失败，请检查配置")
        input("按回车键退出...")
        return
    
    print("✅ 数据库连接成功")
    
    # 设置服务地址
    host = '0.0.0.0'
    port = 8073
    web_url = f"http://{host}:{port}/index.html"
    
    print(f"🚀 正在启动Web服务...")
    print(f"📱 服务地址: {web_url}")
    print()
    print("💡 提示:")
    print("   - 程序启动后会自动打开浏览器")
    print("   - 如果浏览器没有自动打开，请手动访问上述地址")
    print("   - 按 Ctrl+C 可以停止服务")
    print()
    
    # 启动浏览器
    open_browser(web_url, delay=3)
    
    try:
        # 启动Flask服务
        app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")
        logger.info("用户停止服务")
    except Exception as e:
        print(f"\n❌ 服务启动失败: {e}")
        logger.error(f"服务启动失败: {e}")
        input("按回车键退出...")
    finally:
        print("👋 服务已停止，感谢使用！")

if __name__ == "__main__":
    main()
