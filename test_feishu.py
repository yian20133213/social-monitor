import requests
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# 获取访问令牌
def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": os.getenv("FEISHU_APP_ID"),
        "app_secret": os.getenv("FEISHU_APP_SECRET")
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    token_data = response.json()
    print("获取Token结果:", token_data)
    return token_data.get("tenant_access_token")


# 测试添加一条记录
def test_add_record():
    token = get_tenant_access_token()
    if not token:
        print("获取token失败，请检查APP_ID和APP_SECRET")
        return

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{os.getenv('FEISHU_BITABLE_ID')}/tables/{os.getenv('FEISHU_TABLE_ID')}/records"

    # 测试数据 - 根据您的表格结构调整
    payload = {
        "fields": {
            "账号名称": "test_account",
            "内容": "这是一条测试内容，用于验证API连接是否正常工作",
            "点赞数": 100,
            "转发数": 50,
            "评论数": 25
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    print("添加记录结果:", response.status_code)
    print(response.json())


if __name__ == "__main__":
    test_add_record()