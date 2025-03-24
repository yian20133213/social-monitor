import os
import requests
import json
import logging
import re
import argparse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("coordinator/scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置
WEB_SCRAPER_MCP_URL = os.getenv('WEB_SCRAPER_MCP_URL', 'http://localhost:3001')
FEISHU_MCP_URL = os.getenv('FEISHU_MCP_URL', 'http://localhost:3002')

# 平台配置
SUPPORTED_PLATFORMS = {
    'twitter': {
        'name': 'Twitter/X',
        'base_url': 'https://twitter.com/'
    },
    'xiaohongshu': {
        'name': '小红书',
        'base_url': 'https://www.xiaohongshu.com/user/profile/'
    }
    # 预留扩展其他平台的位置
}

def parse_target_accounts():
    """解析目标账号配置"""
    target_accounts = {}
    
    # 从TARGET_ACCOUNTS环境变量解析
    accounts_str = os.getenv('TARGET_ACCOUNTS', '')
    if accounts_str:
        for account in accounts_str.split(','):
            account = account.strip()
            if ':' in account:
                platform, username = account.split(':', 1)
                if platform in SUPPORTED_PLATFORMS:
                    if platform not in target_accounts:
                        target_accounts[platform] = []
                    target_accounts[platform].append(username)
            else:
                # 默认为Twitter账号
                if 'twitter' not in target_accounts:
                    target_accounts['twitter'] = []
                target_accounts['twitter'].append(account)
    
    # 从平台特定环境变量解析
    for platform in SUPPORTED_PLATFORMS.keys():
        env_var = f"{platform.upper()}_ACCOUNTS"
        accounts_str = os.getenv(env_var, '')
        if accounts_str:
            accounts = [account.strip() for account in accounts_str.split(',') if account.strip()]
            if platform not in target_accounts:
                target_accounts[platform] = []
            target_accounts[platform].extend(accounts)
    
    return target_accounts

def get_scrape_tool():
    """获取web-scraper-mcp的抓取工具"""
    try:
        response = requests.post(
            f"{WEB_SCRAPER_MCP_URL}/tools",
            json={}
        )
        
        tools = response.json().get("tools", [])
        for tool in tools:
            if "scrape" in tool.get("operation_id", "").lower() or "fetch" in tool.get("operation_id", "").lower():
                return tool
        
        logger.error("未找到合适的网页抓取工具")
        return None
    except Exception as e:
        logger.error(f"获取抓取工具时出错: {str(e)}")
        return None

def scrape_twitter_profile(username, scrape_tool):
    """抓取Twitter个人页面内容"""
    try:
        if not scrape_tool:
            logger.error("抓取工具未初始化")
            return []
        
        # 使用工具抓取Twitter页面
        operation_id = scrape_tool["operation_id"]
        response = requests.post(
            f"{WEB_SCRAPER_MCP_URL}/tools/{operation_id}",
            json={
                "parameters": {
                    "url": f"https://twitter.com/{username}",
                    "selector": "article" # Twitter帖子选择器
                }
            }
        )
        
        if response.status_code != 200:
            logger.error(f"获取Twitter页面失败: {response.status_code}")
            return []
        
        result = response.json().get("result", {})
        html_content = result.get("html", "")
        if not html_content:
            logger.error("返回的Twitter HTML内容为空")
            return []
        
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        return extract_tweets(soup, username)
    except Exception as e:
        logger.error(f"抓取Twitter页面出错: {str(e)}")
        return []

def extract_tweets(soup, username):
    """从HTML中提取推文信息"""
    tweets = []
    
    # Twitter文章元素
    tweet_elements = soup.select('article')
    
    for element in tweet_elements[:10]:  # 获取最新的10条
        try:
            # 提取推文内容
            content_element = element.select_one('div[data-testid="tweetText"]')
            content = content_element.get_text() if content_element else ""
            
            # 提取时间
            time_element = element.select_one('time')
            timestamp = time_element['datetime'] if time_element and 'datetime' in time_element.attrs else ""
            
            # 提取互动数据
            likes = 0
            retweets = 0
            replies = 0
            
            stat_elements = element.select('span[data-testid$="-count"]')
            for stat in stat_elements:
                text = stat.get_text().strip()
                if 'like' in stat['data-testid']:
                    likes = convert_stat_to_number(text)
                elif 'retweet' in stat['data-testid']:
                    retweets = convert_stat_to_number(text)
                elif 'reply' in stat['data-testid']:
                    replies = convert_stat_to_number(text)
            
            tweets.append({
                "content": content,
                "timestamp": timestamp or datetime.now().isoformat(),
                "likes": likes,
                "retweets": retweets,
                "replies": replies,
                "username": username,
                "collected_at": datetime.now().isoformat(),
                "platform": "twitter"
            })
        except Exception as e:
            logger.warning(f"提取推文时出错: {str(e)}")
            continue
    
    return tweets

def scrape_xiaohongshu_profile(username, scrape_tool):
    """抓取小红书个人页面内容"""
    try:
        if not scrape_tool:
            logger.error("抓取工具未初始化")
            return []
        
        # 使用工具抓取小红书页面
        operation_id = scrape_tool["operation_id"]
        response = requests.post(
            f"{WEB_SCRAPER_MCP_URL}/tools/{operation_id}",
            json={
                "parameters": {
                    "url": f"https://www.xiaohongshu.com/user/profile/{username}",
                    "selector": ".note-item" # 小红书笔记选择器
                }
            }
        )
        
        if response.status_code != 200:
            logger.error(f"获取小红书页面失败: {response.status_code}")
            return []
        
        result = response.json().get("result", {})
        html_content = result.get("html", "")
        if not html_content:
            logger.error("返回的小红书HTML内容为空")
            return []
        
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        return extract_xiaohongshu_notes(soup, username)
    except Exception as e:
        logger.error(f"抓取小红书页面出错: {str(e)}")
        return []

def extract_xiaohongshu_notes(soup, username):
    """从HTML中提取小红书笔记信息"""
    notes = []
    
    # 小红书笔记元素
    note_elements = soup.select('.note-item')
    
    for element in note_elements[:10]:  # 获取最新的10条
        try:
            # 提取笔记内容
            title_element = element.select_one('.title')
            title = title_element.get_text().strip() if title_element else ""
            
            desc_element = element.select_one('.desc')
            desc = desc_element.get_text().strip() if desc_element else ""
            
            content = f"{title}\n{desc}" if desc else title
            
            # 提取时间
            time_element = element.select_one('.time')
            timestamp = time_element.get_text().strip() if time_element else ""
            if timestamp:
                try:
                    # 解析时间格式
                    if '分钟前' in timestamp:
                        minutes = int(timestamp.replace('分钟前', '').strip())
                        timestamp = (datetime.now().replace(microsecond=0) - timedelta(minutes=minutes)).isoformat()
                    elif '小时前' in timestamp:
                        hours = int(timestamp.replace('小时前', '').strip())
                        timestamp = (datetime.now().replace(microsecond=0) - timedelta(hours=hours)).isoformat()
                    elif '天前' in timestamp:
                        days = int(timestamp.replace('天前', '').strip())
                        timestamp = (datetime.now().replace(microsecond=0) - timedelta(days=days)).isoformat()
                    else:
                        # 直接解析日期
                        timestamp = datetime.strptime(timestamp, '%Y-%m-%d').isoformat()
                except Exception as e:
                    logger.warning(f"解析小红书时间戳出错: {str(e)}")
                    timestamp = datetime.now().isoformat()
            else:
                timestamp = datetime.now().isoformat()
            
            # 提取互动数据
            likes = 0
            comments = 0
            
            like_element = element.select_one('.like span')
            if like_element:
                likes = convert_stat_to_number(like_element.get_text().strip())
            
            comment_element = element.select_one('.comment span')
            if comment_element:
                comments = convert_stat_to_number(comment_element.get_text().strip())
            
            notes.append({
                "content": content,
                "timestamp": timestamp,
                "likes": likes,
                "comments": comments,
                "shares": 0,  # 小红书一般不显示分享数
                "username": username,
                "collected_at": datetime.now().isoformat(),
                "platform": "xiaohongshu"
            })
        except Exception as e:
            logger.warning(f"提取小红书笔记时出错: {str(e)}")
            continue
    
    return notes

def convert_stat_to_number(text):
    """将形如'1.2K'、'3.5万'的文本转换为数字"""
    try:
        if not text:
            return 0
        text = text.strip().lower()
        if 'k' in text:
            return int(float(text.replace('k', '')) * 1000)
        if 'm' in text:
            return int(float(text.replace('m', '')) * 1000000)
        if 'w' in text or '万' in text:  # 处理中文的"万"
            text = text.replace('w', '').replace('万', '')
            return int(float(text) * 10000)
        return int(text) if text else 0
    except:
        return 0

def format_for_feishu(items):
    """将多平台内容数据格式化为飞书多维表格格式"""
    records = []
    
    for item in items:
        platform = item.get("platform", "未知平台")
        
        # 计算互动总量
        interaction_total = 0
        
        # 根据不同平台计算互动总量
        if platform == "twitter":
            interaction_total = item.get("likes", 0) + item.get("retweets", 0) + item.get("replies", 0)
        elif platform == "xiaohongshu":
            interaction_total = item.get("likes", 0) + item.get("comments", 0)
        
        # 内容分类逻辑
        content_type = []
        content = item.get("content", "").lower()
        
        # 通用关键词匹配
        if any(word in content for word in ["发布", "推出", "新品", "发售", "上线"]):
            content_type.append("产品宣传")
        if any(word in content for word in ["活动", "直播", "预告", "抽奖", "揭晓"]):
            content_type.append("活动通知")
        if any(word in content for word in ["谢谢", "感谢", "我们", "用户", "粉丝"]):
            content_type.append("用户互动")
        
        # AI相关内容识别
        if any(word in content for word in ["ai", "人工智能", "机器学习", "深度学习", "神经网络", "大语言模型", "llm", "gpt"]):
            content_type.append("AI相关")
        
        # 如果没有匹配到类型，则标记为"其他"
        if not content_type:
            content_type.append("其他")
        
        # 根据不同平台映射互动数据
        likes = 0
        comments = 0
        shares = 0
        
        if platform == "twitter":
            likes = item.get("likes", 0)
            comments = item.get("replies", 0)
            shares = item.get("retweets", 0)
        elif platform == "xiaohongshu":
            likes = item.get("likes", 0)
            comments = item.get("comments", 0)
        
        # 创建飞书记录
        records.append({
            "fields": {
                "账号名称": item.get("username", ""),
                "内容": item.get("content", ""),
                "发布时间": item.get("timestamp", datetime.now().isoformat()),
                "点赞数": likes,
                "评论数": comments,
                "转发数": shares,
                "平台": get_platform_display_name(platform),
                "收集时间": item.get("collected_at", datetime.now().isoformat()),
                "互动总量": interaction_total,
                "内容类型": content_type,
                "敏感度": "低"  # 默认值，后续可人工修改
            }
        })
    
    return records

def get_platform_display_name(platform_key):
    """获取平台的显示名称"""
    for key, config in SUPPORTED_PLATFORMS.items():
        if key == platform_key:
            return config.get('name', platform_key)
    return platform_key

def send_to_feishu(records):
    """发送数据到飞书多维表格"""
    if not records:
        logger.info("没有数据需要发送")
        return
        
    try:
        logger.info(f"正在发送{len(records)}条记录到飞书")
        response = requests.post(
            f"{FEISHU_MCP_URL}/tools/append_to_bitable",
            json={
                "parameters": {
                    "records": records
                }
            }
        )
        
        if response.status_code != 200:
            logger.error(f"发送到飞书失败: HTTP {response.status_code}")
            return
            
        result = response.json()
        logger.info(f"发送到飞书结果: {result}")
    except Exception as e:
        logger.error(f"发送到飞书出错: {str(e)}")

def load_mock_data():
    """从模拟数据文件加载数据"""
    try:
        mock_file = os.path.join(os.path.dirname(__file__), "mock_data.json")
        with open(mock_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"模拟数据文件不存在，尝试生成新的模拟数据")
        try:
            # 尝试导入模拟数据生成模块
            from mock_data import generate_mock_twitter_data, generate_mock_xiaohongshu_data
            
            all_items = []
            # 生成Twitter模拟数据
            twitter_accounts = ["OpenAI", "AnthropicAI", "GoogleAI"]
            for account in twitter_accounts:
                all_items.extend(generate_mock_twitter_data(account, count=3))
            
            # 生成小红书模拟数据
            xiaohongshu_accounts = ["AI博主", "科技评测", "程序员日常"]
            for account in xiaohongshu_accounts:
                all_items.extend(generate_mock_xiaohongshu_data(account, count=3))
                
            # 保存模拟数据
            with open(mock_file, 'w', encoding='utf-8') as f:
                json.dump(all_items, f, ensure_ascii=False, indent=2)
                
            return all_items
        except ImportError:
            logger.error("无法导入mock_data模块，无法生成模拟数据")
            return []
    except json.JSONDecodeError:
        logger.error("模拟数据文件格式无效")
        return []

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='对标账号数据采集工具')
    parser.add_argument('--test-mode', action='store_true', help='使用测试模式(模拟数据)')
    parser.add_argument('--mock-only', action='store_true', help='只生成模拟数据，不发送到飞书')
    args = parser.parse_args()
    
    # 确保日志目录存在
    os.makedirs("coordinator", exist_ok=True)
    
    all_items = []
    
    if args.test_mode:
        logger.info("使用测试模式，加载模拟数据")
        all_items = load_mock_data()
        logger.info(f"已加载{len(all_items)}条模拟数据")
    else:
        # 解析目标账号
        target_accounts = parse_target_accounts()
        logger.info(f"已配置的目标账号: {target_accounts}")
        
        # 获取抓取工具
        scrape_tool = get_scrape_tool()
        if not scrape_tool:
            logger.error("无法获取抓取工具，切换到测试模式")
            all_items = load_mock_data()
        else:
            # 处理Twitter账号
            if 'twitter' in target_accounts:
                twitter_accounts = target_accounts['twitter']
                logger.info(f"开始抓取{len(twitter_accounts)}个Twitter账号")
                
                for username in twitter_accounts:
                    logger.info(f"正在抓取Twitter账号: {username}")
                    tweets = scrape_twitter_profile(username, scrape_tool)
                    logger.info(f"已获取{len(tweets)}条推文")
                    all_items.extend(tweets)
            
            # 处理小红书账号
            if 'xiaohongshu' in target_accounts:
                xiaohongshu_accounts = target_accounts['xiaohongshu']
                logger.info(f"开始抓取{len(xiaohongshu_accounts)}个小红书账号")
                
                for username in xiaohongshu_accounts:
                    logger.info(f"正在抓取小红书账号: {username}")
                    notes = scrape_xiaohongshu_profile(username, scrape_tool)
                    logger.info(f"已获取{len(notes)}条笔记")
                    all_items.extend(notes)
    
    # 数据存储和发送
    if all_items:
        # 格式化数据并发送到飞书
        feishu_records = format_for_feishu(all_items)
        
        if not args.mock_only:
            send_to_feishu(feishu_records)
        else:
            logger.info("模拟模式：跳过发送到飞书的步骤")
        
        # 保存到本地文件作为备份
        backup_dir = "coordinator/backup"
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = f"{backup_dir}/social_media_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(all_items, f, ensure_ascii=False, indent=2)
            logger.info(f"备份数据保存到: {backup_file}")
        
        logger.info(f"成功收集和处理了{len(all_items)}条内容")
    else:
        logger.warning("未获取到任何内容")

if __name__ == "__main__":
    main()
