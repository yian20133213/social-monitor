@echo off
echo 启动监控系统...

echo 启动配置服务器...
start /b cmd /c "python config_server.py"

echo 启动网页抓取MCP服务器...
start /b cmd /c "cd web-scraper-mcp && node src/index.js"

echo 启动飞书MCP服务器...
start /b cmd /c "cd feishu-mcp && node index.js"

echo 等待服务启动...
timeout /t 5

echo 请打开浏览器访问 http://localhost:8080 配置对标账号
echo 服务已经启动完成，现在可以运行对标账号监控脚本

:menu
echo.
echo 菜单选项:
echo 1. 打开对标账号配置页面
echo 2. 运行数据采集脚本
echo 3. 退出程序
echo.
set /p choice=请选择操作 (1/2/3): 

if "%choice%"=="1" (
    start http://localhost:8080
    goto menu
) else if "%choice%"=="2" (
    echo 运行协调脚本...
    python coordinator/scraper.py
    goto menu
) else if "%choice%"=="3" (
    echo 关闭所有服务...
    taskkill /f /im node.exe
    taskkill /f /im python.exe
    echo 程序已退出
    exit
) else (
    echo 无效选择，请重新输入
    goto menu
)