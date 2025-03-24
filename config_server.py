import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv, set_key
import urllib.parse

# 配置
CONFIG_PORT = 8080
ENV_FILE_PATH = ".env"

# 加载环境变量
load_dotenv(ENV_FILE_PATH)

class ConfigHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type='text/html'):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            # 返回配置页面
            with open('config.html', 'rb') as file:
                self._set_headers()
                self.wfile.write(file.read())
        
        elif self.path == '/get-target-accounts':
            # 获取环境变量中的目标账号配置
            config = {
                'twitter': os.getenv('TWITTER_ACCOUNTS', '').split(',') if os.getenv('TWITTER_ACCOUNTS') else [],
                'xiaohongshu': os.getenv('XIAOHONGSHU_ACCOUNTS', '').split(',') if os.getenv('XIAOHONGSHU_ACCOUNTS') else []
            }
            
            # 过滤空值
            for platform in config:
                config[platform] = [account for account in config[platform] if account]
            
            self._set_headers('application/json')
            self.wfile.write(json.dumps(config).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/save-target-accounts':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            config = json.loads(post_data.decode('utf-8'))
            
            # 更新环境变量文件
            with open(ENV_FILE_PATH, 'r') as file:
                env_content = file.read()
            
            # 提取已有的非账号配置
            env_lines = env_content.splitlines()
            preserved_lines = []
            for line in env_lines:
                if not (line.startswith('TWITTER_ACCOUNTS=') or 
                        line.startswith('XIAOHONGSHU_ACCOUNTS=') or 
                        line.startswith('TARGET_ACCOUNTS=')):
                    preserved_lines.append(line)
            
            # 添加新的账号配置
            for var_name, value in config.items():
                if value:  # 只添加非空值
                    preserved_lines.append(f"{var_name}={value}")
            
            # 写回环境变量文件
            with open(ENV_FILE_PATH, 'w') as file:
                file.write('\n'.join(preserved_lines))
            
            # 重新加载环境变量
            load_dotenv(ENV_FILE_PATH, override=True)
            
            self._set_headers('application/json')
            self.wfile.write(json.dumps({'success': True, 'message': '配置已保存'}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server_address = ('', CONFIG_PORT)
    httpd = HTTPServer(server_address, ConfigHandler)
    print(f'配置服务器运行在 http://localhost:{CONFIG_PORT}')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
