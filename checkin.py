import os
import asyncio
from playwright.async_api import async_playwright

USERNAME = os.environ.get('FREECLOUD_USER')
PASSWORD = os.environ.get('FREECLOUD_PASS')
BASE_URL = "https://panel.freecloud.ltd"

async def run():
    async with async_playwright() as p:
        # 进一步模拟真实浏览器：添加更多的启动参数
        browser = await p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--ignore-certificate-errors'
        ])
        
        # 模拟高分辨率真实屏幕
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai"
        )
        page = await context.new_page()

        print("🛡️ 正在尝试绕过 Cloudflare 安全屏障...")
        try:
            # 直接尝试访问登录接口，减少首页跳转
            await page.goto(f"{BASE_URL}/clientarea.php", wait_until="domcontentloaded")
            
            # 暴力等待：Cloudflare 盾有时需要极长时间处理数据中心 IP
            for i in range(1, 11): # 增加到 50 秒总时长
                print(f"⏳ 等待中... ({i*5}s)")
                await asyncio.sleep(5)
                # 检查是否出现了用户名输入框，或者是否已经因为有 Cookie 直接进入了后台
                if await page.query_selector('input[name="username"]') or "退出" in await page.content():
                    break
            
            if await page.query_selector('input[name="username"]'):
                print("✅ 发现登录框，开始执行登录...")
                await page.fill('input[name="username"]', USERNAME)
                await page.fill('input[name="password"]', PASSWORD)
                await page.click('input[type="submit"], button[type="submit"]')
                await page.wait_for_load_state("networkidle")
            
            # 签到核心逻辑：WHMCS 签到动作
            print("🚀 正在执行签到指令...")
            # 绕过 UI 直接访问签到 API 路径
            await page.goto(f"{BASE_URL}/clientarea.php?action=checkin", wait_until="networkidle")
            
            # 检查最终页面内容
            await page.goto(f"{BASE_URL}/clientarea.php", wait_until="networkidle")
            final_html = await page.content()
            
            if "您今天已经签到过了" in final_html or "积分" in final_html:
                print("🎉 任务执行成功！已进入会员中心或确认已签到。")
            else:
                print("❌ 未能确认签到结果，请检查截图。")
                await page.screenshot(path="final_state.png")

        except Exception as e:
            print(f"⚠️ 运行时异常: {str(e)}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
