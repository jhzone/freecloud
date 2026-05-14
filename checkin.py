import requests
import re
import os

# 从 GitHub Secrets 中读取配置
USERNAME = os.environ.get('FREECLOUD_USER')
PASSWORD = os.environ.get('FREECLOUD_PASS')
BASE_URL = "https://panel.freecloud.ltd"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

def start():
    try:
        # 1. 访问登录页获取隐藏的 CSRF Token
        login_page_res = session.get(f"{BASE_URL}/login")
        token_match = re.search(r'name="token" value="(.+?)"', login_page_res.text)
        token = token_match.group(1) if token_match else ""

        # 2. 提交登录请求
        login_data = {
            "token": token,
            "username": USERNAME,
            "password": PASSWORD
        }
        res = session.post(f"{BASE_URL}/dologin.php", data=login_data)

        # 3. 验证是否登录成功
        if "Logout" in res.text or "退出" in res.text or "clientarea.php" in res.url:
            print("✅ 登录成功！")
            
            # 4. 执行签到动作
            # 注意：根据 WHMCS 插件习惯，签到 URL 通常是以下几种之一，脚本会依次尝试
            checkin_urls = [
                f"{BASE_URL}/index.php?m=spotlight_checkin", # 常见插件路径
                f"{BASE_URL}/clientarea.php?action=checkin",
                f"{BASE_URL}/plugin.php?id=checkin"
            ]
            
            for url in checkin_urls:
                check_res = session.get(url)
                if "签到成功" in check_res.text or "已经签到" in check_res.text:
                    print(f"🎯 签到结果: {url} 访问成功")
                    break
            
            # 5. 最后访问首页确认积分状态
            final_res = session.get(f"{BASE_URL}/clientarea.php")
            # 匹配截图中的积分余额部分
            balance = re.search(r'您的账户余额为：(.*?)积分', final_res.text)
            if balance:
                print(f"💰 当前账户余额: {balance.group(1).strip()} 积分")
            if "您今天已经签到过了" in final_res.text:
                print("✨ 确认结果：今日已完成签到。")
        else:
            print("❌ 登录失败，请检查 Secret 中的账号密码是否正确。")

    except Exception as e:
        print(f"⚠️ 脚本运行出错: {str(e)}")

if __name__ == "__main__":
    start()
