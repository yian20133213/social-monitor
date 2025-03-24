require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');

const app = express();
app.use(bodyParser.json());

// 飞书API配置
const FEISHU_APP_ID = process.env.FEISHU_APP_ID;
const FEISHU_APP_SECRET = process.env.FEISHU_APP_SECRET;
const FEISHU_BITABLE_ID = process.env.FEISHU_BITABLE_ID;
const FEISHU_TABLE_ID = process.env.FEISHU_TABLE_ID;

// 获取飞书访问令牌
async function getAccessToken() {
  try {
    const response = await axios.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', {
      app_id: FEISHU_APP_ID,
      app_secret: FEISHU_APP_SECRET
    });
    return response.data.tenant_access_token;
  } catch (error) {
    console.error('获取飞书令牌失败:', error);
    throw error;
  }
}

// MCP工具定义
app.post('/tools', (req, res) => {
  res.json({
    tools: [
      {
        operation_id: 'append_to_bitable',
        description: '添加数据到飞书多维表格',
        parameters: {
          type: 'object',
          properties: {
            records: {
              type: 'array',
              description: '要添加的记录数组',
              items: {
                type: 'object'
              }
            }
          },
          required: ['records']
        },
        returns: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            message: { type: 'string' }
          }
        }
      }
    ]
  });
});

// MCP工具实现
app.post('/tools/:operation_id', async (req, res) => {
  if (req.params.operation_id === 'append_to_bitable') {
    try {
      const token = await getAccessToken();
      const { records } = req.body.parameters;
      
      const response = await axios.post(
        `https://open.feishu.cn/open-apis/bitable/v1/apps/${FEISHU_BITABLE_ID}/tables/${FEISHU_TABLE_ID}/records/batch_create`,
        { records },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      res.json({
        result: {
          success: true,
          message: `成功添加${records.length}条记录`,
          details: response.data
        }
      });
    } catch (error) {
      res.json({
        result: {
          success: false,
          message: error.message
        }
      });
    }
  } else {
    res.status(400).json({ error: '未知操作' });
  }
});

const PORT = process.env.PORT || 3002;
app.listen(PORT, () => {
  console.log(`飞书MCP服务运行在端口 ${PORT}`);
});