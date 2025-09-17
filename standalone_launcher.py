#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
北斗卫星状态监控系统 - 独立启动器
这个版本不需要打包，直接运行Python脚本
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_python():
    """检查Python环境"""
    try:
        version = sys.version_info
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    except:
        print("❌ Python环境检查失败")
        return False

def install_requirements():
    """安装依赖包"""
    requirements = [
        "Flask>=2.0.0",
        "Flask-CORS>=3.0.0", 
        "oracledb>=1.0.0"
    ]
    
    print("🔄 正在检查并安装依赖包...")
    for req in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", req], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
            print(f"✅ {req.split('>=')[0]} 安装完成")
        except subprocess.CalledProcessError:
            print(f"❌ {req} 安装失败")
            return False
    return True

def start_web_service():
    """启动Web服务"""
    try:
        # 确保在正确的目录中
        current_dir = Path(__file__).parent
        os.chdir(current_dir)
        
        # 检查必要文件
        if not (current_dir / "oracle_concurrent_executor.py").exists():
            print("❌ 找不到 oracle_concurrent_executor.py 文件")
            return False
            
        if not (current_dir / "index.html").exists():
            print("❌ 找不到 index.html 文件")
            return False
        
        print("✅ 文件检查完成")
        
        # 启动Python服务
        print("🚀 正在启动Web服务...")
        print("📱 服务地址: http://127.0.0.1:8071/index.html")
        print()
        print("💡 提示:")
        print("   - 3秒后会自动打开浏览器")
        print("   - 如果浏览器没有自动打开，请手动访问上述地址")
        print("   - 按 Ctrl+C 可以停止服务")
        print()
        
        # 延迟启动浏览器
        def open_browser():
            time.sleep(3)
            try:
                webbrowser.open("http://127.0.0.1:8071/index.html")
                print("🌐 浏览器已启动")
            except:
                print("⚠️ 无法自动打开浏览器，请手动访问")
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动Flask应用
        subprocess.run([sys.executable, "oracle_concurrent_executor.py"])
        
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False
        
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("           北斗卫星状态监控系统")
    print("           独立启动器 (无需打包)")
    print("=" * 60)
    print()
    
    # 检查Python环境
    if not check_python():
        input("按回车键退出...")
        return
    
    # 安装依赖
    if not install_requirements():
        print("❌ 依赖安装失败，请检查网络连接")
        input("按回车键退出...")
        return
    
    # 启动服务
    if not start_web_service():
        print("❌ 服务启动失败")
        input("按回车键退出...")
        return
    
    print("👋 感谢使用！")

if __name__ == "__main__":
    main()