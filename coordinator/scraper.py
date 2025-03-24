import os
import requests
import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置
WEB_SCRAPER_MCP_URL = os.getenv('WEB_SCRAPER_MCP_URL', 'http://localhost:3001')
FEISHU_MCP_URL = os.getenv('FEISHU_MCP_URL', 'http://localhost:3002')
TARGET_ACCOUNTS = os.getenv('TARGET_ACCOUNTS', 'competitor1,competitor2').split(',')

def scrape_twitter_profile(username):
    """抓取Twitter个人页面内容"""
    try:
        # 使用web-scraper-mcp服务器请求Twitter页面
        # 注意: web-scraper-mcp可能使用不同的操作名称，请根据实际情况调整
        response = requests.post(
            f"{WEB_SCRAPER_MCP_URL}/tools",
            json={}
        )
        
        # 获取工具列表
        tools = response.json().get("tools", [])
        
        # 查找适合的网页抓取工具
        scrape_tool = None
        for tool in tools:
            if "scrape" in tool.get("operation_id", "").lower() or "fetch" in tool.get("operation_id", "").lower():
                scrape_tool = tool
                break
        
        if not scrape_tool:
            logger.error("未找到合适的网页抓取工具")
            return []
        
        # 使用找到的工具抓取网页
        operation_id = scrape_tool["operation_id"]
        response = requests.post(
            f"{WEB_SCRAPER_MCP_URL}/tools/{operation_id}",
            json={
                "parameters": {
                    "url": f"https://twitter.com/{username}",
                    "selector": "article" # 可根据实际需要调整选择器
                }
            }
        )
        
        if response.status_code != 200:
            logger.error(f"获取页面失败: {response.status_code}")
            return []
        
        result = response.json().get("result", {})
        html_content = result.get("html", "")
        if not html_content:
            logger.error("返回的HTML内容为空")
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
    
    # 根据web-scraper-mcp返回的HTML结构调整选择器
    tweet_elements = soup.select('article')
    
    for element in tweet_elements[:10]:  # 只取最新的10条
        try:
            # 尝试提取推文内容 - 根据实际HTML结构调整选择器
            content_element = element.select_one('div[data-testid="tweetText"]')
            content = content_element.get_text() if content_element else ""
            
            # 时间提取 - 根据实际HTML结构调整
            time_element = element.select_one('time')
            timestamp = time_element['datetime'] if time_element and 'datetime' in time_element.attrs else ""
            
            # 提取互动数据 - 根据实际HTML结构调整
            likes = 0
            retweets = 0
            replies = 0
            
            # 尝试查找互动数据元素
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
                "collected_at": datetime.now().isoformat()
            })
        except Exception as e:
            logger.warning(f"提取推文时出错: {str(e)}")
            continue
    
    return tweets

def convert_stat_to_number(text):
    """将形如'1.2K'的文本转换为数字"""
    try:
        if not text:
            return 0
        text = text.strip().lower()
        if 'k' in text:
            return int(float(text.replace('k', '')) * 1000)
        if 'm' in text:
            return int(float(text.replace('m', '')) * 1000000)
        return int(text) if text else 0
    except:
        return 0

def format_for_feishu(tweets):
    """将推文数据格式化为飞书多维表格格式"""
    records = []
    
    for tweet in tweets:
        # 默认设置平台为Twitter/X
        platform = "Twitter/X"
        
        # 计算互动总量
        interaction_total = tweet["likes"] + tweet["retweets"] + tweet["replies"]
        
        # 简单内容分类逻辑(示例)
        content_type = []
        if any(word in tweet["content"].lower() for word in ["发布", "推出", "新品"]):
            content_type.append("产品宣传")
        if any(word in tweet["content"].lower() for word in ["活动", "直播", "预告"]):
            content_type.append("活动通知")
        if any(word in tweet["content"].lower() for word in ["谢谢", "感谢", "我们", "用户"]):
            content_type.append("用户互动")
        if not content_type:
            content_type.append("其他")
        
        records.append({
            "fields": {
                "账号名称": tweet["username"],
                "内容": tweet["content"],
                "发布时间": tweet["timestamp"],
                "点赞数": tweet["likes"],
                "转发数": tweet["retweets"],
                "评论数": tweet["replies"],
                "平台": platform,
                "收集时间": tweet["collected_at"],
                "互动总量": interaction_total,
                "内容类型": content_type,
                "敏感度": "低"  # 默认值，后续可人工修改
            }
        })
    
    return records

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

def main():
    """主函数"""
    all_tweets = []
    
    # 抓取每个目标账号的数据
    for account in TARGET_ACCOUNTS:
        logger.info(f"正在抓取账号 {account} 的数据")
        tweets = scrape_twitter_profile(account)
        logger.info(f"已获取 {len(tweets)} 条推文")
        all_tweets.extend(tweets)
    
    # 格式化数据并发送到飞书
    if all_tweets:
        feishu_records = format_for_feishu(all_tweets)
        send_to_feishu(feishu_records)
        
        # 保存到本地文件作为备份
        with open(f"../data/tweets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w', encoding='utf-8') as f:
            json.dump(all_tweets, f, ensure_ascii=False, indent=2)
    else:
        logger.warning("未获取到任何推文数据")

if __name__ == "__main__":
    main()