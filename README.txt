北斗卫星状态监控系统 - 便携式部署包

部署步骤：
1. 将此文件夹复制到Windows服务器
2. 在服务器上安装Python 3.8+
3. 双击运行 start.bat
4. 系统会自动安装依赖并启动服务
5. 浏览器访问 http://127.0.0.1:8071/index.html

文件说明：
- start.bat: 启动脚本
- standalone_launcher.py: 独立启动器
- oracle_concurrent_executor.py: 主服务程序
- index.html: Web界面
- requirements.txt: 依赖列表

注意事项：
1. 确保服务器能访问Oracle数据库
2. 确保端口8071未被占用
3. 修改oracle_concurrent_executor.py中的数据库配置
