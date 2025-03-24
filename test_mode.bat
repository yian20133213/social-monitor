@echo off
echo 启动对标账号测试模式...

echo 第一步: 生成模拟测试数据
python coordinator/mock_data.py

echo 第二步: 使用测试模式运行数据采集脚本
python coordinator/scraper.py --test-mode

echo.
echo 测试完成！模拟数据已生成并处理
echo 您可以检查 coordinator/backup 目录查看备份的数据文件
echo.
echo 注意：此测试模式不依赖web-scraper-mcp服务，仅使用模拟数据进行测试

pause
