@echo off
echo 启动网页抓取MCP服务器...
start /b cmd /c "cd servers\src\fetch && node server.js"

echo 启动飞书MCP服务器...
start /b cmd /c "cd feishu-mcp && node index.js"

echo 等待服务启动...
timeout /t 5

echo 运行协调脚本...
cd coordinator
python scraper.py

echo 数据收集完成
echo 请手动关闭服务窗口