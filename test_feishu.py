import requests
import os
import json
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("feishu_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

    try:
        logger.info(f"请求获取tenant_access_token，APP_ID: {os.getenv('FEISHU_APP_ID')}")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # 抛出HTTP错误以便捕获
        token_data = response.json()
        logger.info(f"获取Token结果: {token_data}")
        
        # 检查响应中是否有错误码
        if "code" in token_data and token_data["code"] != 0:
            logger.error(f"获取Token错误: {token_data.get('msg', '未知错误')}")
            logger.error(f"错误详情: {token_data}")
            return None
            
        return token_data.get("tenant_access_token")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP错误: {e}")
        logger.error(f"响应状态码: {response.status_code}")
        try:
            logger.error(f"错误详情: {response.json()}")
        except:
            logger.error(f"响应内容: {response.text}")
        return None
    except Exception as e:
        logger.error(f"获取token时发生异常: {e}")
        return None


# 测试添加一条记录
def test_add_record():
    token = get_tenant_access_token()
    if not token:
        logger.error("获取token失败，请检查APP_ID和APP_SECRET")
        return

    bitable_id = os.getenv('FEISHU_BITABLE_ID')
    table_id = os.getenv('FEISHU_TABLE_ID')
    
    logger.info(f"使用的参数: BITABLE_ID={bitable_id}, TABLE_ID={table_id}")
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{bitable_id}/tables/{table_id}/records"

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

    try:
        logger.info(f"请求URL: {url}")
        logger.info(f"请求头: {headers}")
        logger.info(f"请求体: {json.dumps(payload, ensure_ascii=False)}")
        
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 403:
            logger.error("收到403错误，可能是权限问题")
            logger.error(f"响应内容: {response.text}")
            try:
                error_details = response.json()
                logger.error(f"错误详细信息: {json.dumps(error_details, ensure_ascii=False, indent=2)}")
                # 提取具体的错误码和错误信息
                if "code" in error_details:
                    logger.error(f"错误码: {error_details.get('code')}")
                    logger.error(f"错误消息: {error_details.get('msg', '')}")
                    logger.error(f"错误详情: {error_details.get('error', {}).get('details', {})}")
            except:
                pass
        
        response.raise_for_status()
        result = response.json()
        logger.info("添加记录成功")
        logger.info(json.dumps(result, ensure_ascii=False, indent=2))
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP错误: {e}")
        try:
            logger.error(f"错误详情: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        except:
            logger.error(f"响应内容: {response.text}")
    except Exception as e:
        logger.error(f"添加记录时发生异常: {e}")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("开始执行API测试")
    logger.info("环境变量检查:")
    logger.info(f"FEISHU_APP_ID: {'已设置' if os.getenv('FEISHU_APP_ID') else '未设置'}")
    logger.info(f"FEISHU_APP_SECRET: {'已设置' if os.getenv('FEISHU_APP_SECRET') else '未设置'}")
    logger.info(f"FEISHU_BITABLE_ID: {'已设置' if os.getenv('FEISHU_BITABLE_ID') else '未设置'}")
    logger.info(f"FEISHU_TABLE_ID: {'已设置' if os.getenv('FEISHU_TABLE_ID') else '未设置'}")
    logger.info("-" * 50)
    test_add_record()