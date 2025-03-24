@echo off
echo 启动简化版监控系统...

echo 启动配置服务器...
start cmd /c "python config_server.py"

echo 服务已启动，请访问 http://localhost:8080 配置对标账号

echo.
echo 备注: 简化版仅支持配置功能，暂不支持实时数据采集
echo 您可以关闭此窗口来退出程序
