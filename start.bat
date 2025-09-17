@echo off
echo ===============================================
echo    北斗卫星状态监控系统 - 便携版
echo ===============================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    echo 请下载并安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 正在安装依赖...
pip install -r requirements.txt

echo 正在启动服务...
python standalone_launcher.py

pause
