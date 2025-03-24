import json
import random
from datetime import datetime, timedelta

def generate_mock_twitter_data(username, count=5):
    """生成模拟的Twitter数据"""
    mock_data = []
    
    # 一些可能的内容模板
    content_templates = [
        f"我们很高兴地宣布新的AI功能上线！#{random.choice(['AI', 'MachineLearning', '人工智能'])}",
        f"感谢所有用户的支持和反馈！我们将继续努力改进产品。",
        f"今天在{random.choice(['北京', '上海', '深圳', '硅谷'])}举办了一场精彩的科技活动。",
        f"发布了最新的研究论文，探索{random.choice(['大模型', 'GPT', '强化学习', '计算机视觉'])}的前沿应用。",
        f"招聘！我们正在寻找{random.choice(['AI研究员', '机器学习工程师', '产品经理', 'UI设计师'])}加入我们的团队。"
    ]
    
    for i in range(count):
        # 生成随机的发布时间，最近7天内
        posted_time = datetime.now() - timedelta(
            days=random.randint(0, 6),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # 随机互动数据
        likes = random.randint(100, 10000)
        retweets = random.randint(10, likes // 2)
        replies = random.randint(5, likes // 3)
        
        mock_data.append({
            "content": random.choice(content_templates),
            "timestamp": posted_time.isoformat(),
            "likes": likes,
            "retweets": retweets,
            "replies": replies,
            "username": username,
            "collected_at": datetime.now().isoformat(),
            "platform": "twitter"
        })
    
    return mock_data

def generate_mock_xiaohongshu_data(username, count=5):
    """生成模拟的小红书数据"""
    mock_data = []
    
    # 一些可能的内容模板
    content_templates = [
        f"【测评】最近试用了{random.choice(['ChatGPT Plus', 'Claude', 'Gemini', 'Llama'])}\n真的太好用了！推荐大家尝试！",
        f"分享我的AI绘画作品集\n使用{random.choice(['Midjourney', 'DALL-E', 'Stable Diffusion'])}创作，欢迎交流心得～",
        f"AI时代的学习方法分享\n我是如何利用大语言模型提高效率的",
        f"上手体验了{random.choice(['iOS 18', 'Android 15', 'Windows 12'])}的AI新功能，简直惊艳！",
        f"【干货】程序员必备的5个AI辅助工具，第3个太强了！"
    ]
    
    for i in range(count):
        # 生成随机的发布时间，最近14天内
        posted_time = datetime.now() - timedelta(
            days=random.randint(0, 13),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # 随机互动数据
        likes = random.randint(50, 5000)
        comments = random.randint(5, likes // 4)
        
        mock_data.append({
            "content": random.choice(content_templates),
            "timestamp": posted_time.isoformat(),
            "likes": likes,
            "comments": comments,
            "shares": random.randint(1, likes // 5),
            "username": username,
            "collected_at": datetime.now().isoformat(),
            "platform": "xiaohongshu"
        })
    
    return mock_data

def save_mock_data_to_file(data, filename="mock_data.json"):
    """将模拟数据保存到文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"已保存{len(data)}条模拟数据到 {filename}")
    return filename

def load_mock_data_from_file(filename="mock_data.json"):
    """从文件加载模拟数据"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"文件 {filename} 不存在")
        return []
    except json.JSONDecodeError:
        print(f"文件 {filename} 不是有效的JSON格式")
        return []

if __name__ == "__main__":
    # 生成模拟数据示例
    all_data = []
    
    # Twitter账号数据
    twitter_accounts = ["OpenAI", "AnthropicAI", "DeepMind", "GoogleAI"]
    for account in twitter_accounts:
        all_data.extend(generate_mock_twitter_data(account, count=3))
    
    # 小红书账号数据
    xiaohongshu_accounts = ["用户123456", "AI博主", "科技评测", "程序员日常"]
    for account in xiaohongshu_accounts:
        all_data.extend(generate_mock_xiaohongshu_data(account, count=3))
    
    # 保存到文件
    filename = save_mock_data_to_file(all_data, "coordinator/mock_data.json")
    print(f"可以使用 load_mock_data_from_file('{filename}') 来加载数据")
