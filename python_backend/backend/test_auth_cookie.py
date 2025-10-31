import asyncio
import aiohttp
import json
import sys
import re
from datetime import datetime
import logging
from urllib.parse import urlparse

# 配置详细日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置常量
BASE_URL = "http://localhost:8000"
REGISTER_ENDPOINT = "/auth/register"
LOGIN_ENDPOINT = "/auth/login"
STATS_ENDPOINT = "/game-records/stats"
SESSIONS_ENDPOINT = "/game-records/sessions"

# 测试用户凭据
TEST_USER = {
    "username": "test_user",
    "password": "test_password",
    "email": "test_user@example.com"
}

class AuthCookieTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.success_count = 0
        self.failure_count = 0
        self.access_token = None  # 存储获取到的token
    
    def log_result(self, test_name, success, message=""):
        """记录测试结果"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        status = "✅ PASSED" if success else "❌ FAILED"
        result = f"[{timestamp}] {status} - {test_name}"
        if message:
            result += f"\n  {message}"
        self.test_results.append(result)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        print(result)
    
    async def setup(self):
        """设置测试环境"""
        self.session = aiohttp.ClientSession()
        print("\n🚀 开始测试Cookie认证逻辑...\n")
    
    async def teardown(self):
        """清理测试环境"""
        if self.session:
            await self.session.close()
        
        # 打印测试摘要
        print("\n" + "="*60)
        print("📊 测试结果摘要")
        print("="*60)
        print(f"总测试数: {len(self.test_results)}")
        print(f"通过: {self.success_count}")
        print(f"失败: {self.failure_count}")
        print("\n详细结果:")
        for result in self.test_results:
            print(f"- {result.split(' - ')[1]}")
        print("="*60)
    
    async def test_register_user(self):
        """尝试注册测试用户"""
        test_name = "注册用户测试"
        try:
            # 只使用注册所需的字段
            register_data = {
                "username": TEST_USER["username"],
                "password": TEST_USER["password"],
                "email": TEST_USER["email"]
            }
            
            async with self.session.post(
                f"{BASE_URL}{REGISTER_ENDPOINT}",
                json=register_data,
                allow_redirects=False
            ) as response:
                status = response.status
                # 注册成功(201)或用户已存在(400)都视为成功
                success = status in (201, 400)
                message = f"状态码: {status}"
                self.log_result(test_name, success, message)
                return True
        except Exception as e:
            self.log_result(test_name, False, f"异常: {str(e)}")
            return False
    
    async def test_login_success(self):
        """测试登录成功场景"""
        test_name = "登录成功测试"
        try:
            # 只使用登录所需的字段
            login_data = {
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
            
            print(f"🔍 发送登录请求到: {BASE_URL}{LOGIN_ENDPOINT}")
            print(f"🔍 登录数据: {json.dumps(login_data)}")
            
            async with self.session.post(
                f"{BASE_URL}{LOGIN_ENDPOINT}",
                json=login_data,  # 恢复为JSON格式
                allow_redirects=False
            ) as response:
                status = response.status
                print(f"🔍 登录响应状态码: {status}")
                
                # 尝试获取响应内容
                try:
                    content = await response.json()
                    print(f"🔍 登录响应内容 (JSON): {json.dumps(content)}")
                except:
                    content = await response.text()
                    print(f"🔍 登录响应内容 (Text): {content}")
                
                print(f"🔍 登录响应头: {dict(response.headers)}")
                
                cookies = response.cookies
                
                # 正确处理Morsel对象
                cookie_dict = {}
                cookie_info_lines = []
                
                for key, value in cookies.items():
                    # 将Morsel对象转换为字符串
                    str_value = str(value)
                    cookie_dict[key] = str_value
                    
                    # 记录cookie信息
                    display_value = str_value[:20] + '...' if len(str_value) > 20 else str_value
                    cookie_info_lines.append(f"{key}: {display_value}")
                
                cookie_info = "\n  ".join(cookie_info_lines)
                print(f"🔍 response.cookies内容: {cookie_dict}")
                
                # 打印响应头中的Set-Cookie信息
                set_cookie_headers = response.headers.getall('Set-Cookie', [])
                print(f"🔍 响应头Set-Cookie数量: {len(set_cookie_headers)}")
                for i, cookie in enumerate(set_cookie_headers):
                    print(f"🔍 Set-Cookie[{i}]: {cookie}")
                
                # 从响应头中提取JWT令牌
                jwt_token = None
                for header in set_cookie_headers:
                    if 'access_token=' in header:
                        # 使用正则表达式提取，更可靠
                        match = re.search(r'access_token=([^;]+)', header)
                        if match:
                            jwt_token = match.group(1)
                            print(f"🔍 从响应头提取到JWT令牌: {jwt_token[:30]}...{jwt_token[-10:]}")
                            print(f"🔍 JWT令牌长度: {len(jwt_token)}")
                            
                            # 检查JWT令牌格式（应该有两个点分隔三部分）
                            if '.' in jwt_token:
                                parts = jwt_token.split('.')
                                print(f"🔍 JWT令牌结构: {len(parts)}部分")
                                if len(parts) == 3:
                                    print(f"🔍 JWT令牌格式正确，包含Header.Payload.Signature")
                                else:
                                    print(f"⚠️ JWT令牌格式异常，预期3部分，实际{len(parts)}部分")
                            else:
                                print(f"⚠️ JWT令牌格式异常，不包含点分隔符")
                            break
                
                # 尝试从cookies字典中获取token作为备用
                if not jwt_token and 'access_token' in cookie_dict:
                    jwt_token = cookie_dict['access_token']
                    print(f"🔍 从cookies字典获取JWT令牌作为备用: {jwt_token[:30]}...{jwt_token[-10:]}")
                
                # 保存access_token供后续使用
                self.access_token = jwt_token
                
                # 如果找到了JWT令牌，使用它创建正确的cookie字典
                if jwt_token:
                    correct_cookies = {'access_token': jwt_token}
                    print(f"🔍 使用从响应头提取的JWT令牌作为cookie")
                else:
                    correct_cookies = cookie_dict
                
                # 如果从响应头提取到token，也添加到cookies字典中
                if jwt_token and 'access_token' not in correct_cookies:
                    correct_cookies['access_token'] = jwt_token
                    print(f"🔍 已将从响应头提取的token添加到cookies字典")
                
                success = status == 200
                message = f"状态码: {status}\n  Cookie中包含access_token: {'access_token' in correct_cookies}\n  提取到的JWT令牌: {jwt_token[:30] + '...' if jwt_token else None}"
                self.log_result(test_name, success, message)
                
                print(f"🔍 返回的cookies字典: {correct_cookies}")
                return success, correct_cookies
        except Exception as e:
            self.log_result(test_name, False, f"异常: {str(e)}")
            return False, {}
    
    async def test_access_protected_resource_with_cookie(self, cookies):
        """测试使用Cookie访问受保护资源"""
        test_name = "使用Cookie访问受保护资源测试"
        try:
            # 确保已登录并获取token
            if not self.access_token and 'access_token' in cookies:
                self.access_token = cookies['access_token']
            
            # 使用多种方式测试cookie认证
            # 方法1: 使用headers中的Cookie
            print("\n🔍 测试方法1: 使用headers中的Cookie")
            url = f"{BASE_URL}{STATS_ENDPOINT}"
            token_value = self.access_token or cookies.get('access_token')
            
            # 添加详细的请求头
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": BASE_URL
            }
            
            if token_value:
                headers["Cookie"] = f"access_token={token_value}"
                print(f"🔍 发送请求头 (方法1): {headers}")
            
            # 访问统计信息接口
            async with self.session.get(url, headers=headers) as response1:
                status1 = response1.status
                try:
                    data1 = await response1.json()
                    print(f"🔍 响应状态码 (方法1): {status1}")
                    print(f"🔍 响应内容 (方法1): {json.dumps(data1, ensure_ascii=False)}")
                except:
                    data1 = await response1.text()
                    print(f"🔍 响应状态码 (方法1): {status1}")
                    print(f"🔍 响应内容 (方法1): {data1}")
            
            # 方法2: 使用单独的cookies参数
            print("\n🔍 测试方法2: 使用aiohttp的cookies参数")
            cookies_param = {'access_token': token_value} if token_value else {}
            print(f"🔍 发送cookies参数 (方法2): {cookies_param}")
            
            async with self.session.get(url, headers=headers, cookies=cookies_param) as response2:
                status2 = response2.status
                try:
                    data2 = await response2.json()
                    print(f"🔍 响应状态码 (方法2): {status2}")
                    print(f"🔍 响应内容 (方法2): {json.dumps(data2, ensure_ascii=False)}")
                except:
                    data2 = await response2.text()
                    print(f"🔍 响应状态码 (方法2): {status2}")
                    print(f"🔍 响应内容 (方法2): {data2}")
            
            # 只要有一种方法成功就算通过
            success = status1 == 200 or status2 == 200
            
            message = f"状态码 (方法2): {status2}\n  "
            message += f"方法1状态码: {status1}, 方法2状态码: {status2}\n  "
            message += f"使用的Token: {token_value[:30] + '...' if token_value else None}"
            
            self.log_result(test_name, success, message)
            
            return success
        except Exception as e:
            self.log_result(test_name, False, f"异常: {str(e)}")
            return False
    
    async def test_access_protected_resource_without_credentials(self):
        """测试不带凭据访问受保护资源"""
        test_name = "无凭据访问受保护资源测试"
        try:
            # 创建一个全新的会话，完全不带有任何凭据
            print(f"🔍 创建全新会话进行无凭据测试")
            async with aiohttp.ClientSession() as new_session:
                print(f"🔍 发送无凭据请求到: {BASE_URL}{STATS_ENDPOINT}")
                
                # 明确不携带任何Cookie或认证头
                headers = {"Accept": "application/json"}
                
                async with new_session.get(
                    f"{BASE_URL}{STATS_ENDPOINT}",
                    headers=headers,
                    allow_redirects=False,
                    # 明确设置cookies=None确保不携带任何Cookie
                    cookies=None
                ) as response:
                    status = response.status
                    print(f"🔍 无凭据访问响应状态码: {status}")
                    
                    # 尝试获取响应内容
                    try:
                        content = await response.json()
                        print(f"🔍 无凭据访问响应内容: {json.dumps(content)}")
                    except:
                        content = await response.text()
                        print(f"🔍 无凭据访问响应内容 (Text): {content}")
                    
                    # 期望返回401
                    success = status == 401
                    message = f"状态码: {status}, 期望: 401"
                    self.log_result(test_name, success, message)
                    
                    return success
        except Exception as e:
            print(f"❌ {test_name} 失败: {str(e)}")
            print(f"🔍 错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()  # 打印完整的异常堆栈
            self.log_result(test_name, False, f"异常: {str(e)}")
            return False
    
    async def test_access_multiple_endpoints_with_cookie(self, cookies):
        """测试使用相同Cookie访问多个受保护端点"""
        test_name = "使用Cookie访问多个端点测试"
        try:
            # 确保已登录并获取token
            if not self.access_token and 'access_token' in cookies:
                self.access_token = cookies['access_token']
            
            token_value = self.access_token or cookies.get('access_token')
            
            # 设置请求头，使用Cookie头方式
            headers = {
                "Accept": "application/json",
                "Origin": BASE_URL,
                "Content-Type": "application/json"
            }
            
            if token_value:
                headers["Cookie"] = f"access_token={token_value}"
                print(f"🔍 多端点测试 - 发送的Cookie头: {headers.get('Cookie')}")
            
            # 访问第一个端点 - 统计信息
            url1 = f"{BASE_URL}{STATS_ENDPOINT}"
            print(f"\n🔍 访问第一个端点: {url1}")
            async with self.session.get(url1, headers=headers) as response1:
                status1 = response1.status
                try:
                    data1 = await response1.json()
                    print(f"🔍 第一个端点响应状态码: {status1}")
                    print(f"🔍 第一个端点响应内容: {json.dumps(data1, ensure_ascii=False)}")
                except:
                    data1 = await response1.text()
                    print(f"🔍 第一个端点响应状态码: {status1}")
                    print(f"🔍 第一个端点响应内容: {data1}")
            
            # 访问第二个端点 - 游戏会话
            url2 = f"{BASE_URL}{SESSIONS_ENDPOINT}"
            print(f"\n🔍 访问第二个端点: {url2}")
            async with self.session.get(url2, headers=headers) as response2:
                status2 = response2.status
                try:
                    data2 = await response2.json()
                    print(f"🔍 第二个端点响应状态码: {status2}")
                    print(f"🔍 第二个端点响应内容: {json.dumps(data2, ensure_ascii=False)}")
                except:
                    data2 = await response2.text()
                    print(f"🔍 第二个端点响应状态码: {status2}")
                    print(f"🔍 第二个端点响应内容: {data2}")
            
            # 两个请求都应该成功
            success = status1 == 200 and status2 == 200
            
            message = f"端点1状态码: {status1}, 端点2状态码: {status2}"
            self.log_result(test_name, success, message)
            
            return success
        except Exception as e:
            self.log_result(test_name, False, f"异常: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        await self.setup()
        
        # 先尝试注册用户
        await self.test_register_user()
        
        # 1. 测试登录成功
        login_success, cookies = await self.test_login_success()
        
        if login_success:
            # 2. 使用获取的Cookie访问受保护资源
            await self.test_access_protected_resource_with_cookie(cookies)
            
            # 3. 使用相同Cookie访问多个受保护端点
            await self.test_access_multiple_endpoints_with_cookie(cookies)
        else:
            self.log_result("使用Cookie访问受保护资源测试", False, "跳过: 登录失败")
            self.log_result("使用Cookie访问多个端点测试", False, "跳过: 登录失败")
        
        # 4. 测试不提供凭据访问受保护资源
        await self.test_access_protected_resource_without_credentials()
        
        await self.teardown()

async def main():
    tester = AuthCookieTester()
    await tester.run_all_tests()
    
    # 返回退出码
    return 0 if tester.failure_count == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)