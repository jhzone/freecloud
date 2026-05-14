import os
import asyncio
from playwright.async_api import async_playwright

USERNAME = os.environ.get('FREECLOUD_USER')
PASSWORD = os.environ.get('FREECLOUD_PASS')
BASE_URL = "https://panel.freecloud.ltd"

async def run():
    async with async_playwright() as p:
        # 增加隐身参数，防止被识别为机器人
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True
        )
        page = await context.new_page()

        # 移除 webdriver 标记
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () =>强化 undefined})")

        print("🚀 正在发起请求，挑战 Cloudflare 5秒盾...")
        try:
            # 1. 尝试进入登录页
            await page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
            
            # 增加循环检测，最多等待 30 秒，直到检测到用户名输入框
            success = False
            for i in range(1, 7): # 5秒 * 6次 = 30秒
                print(f"⏳ 正在等待验证重定向 (第 {i*5} 秒)...")
                await asyncio.sleep(5)
                if await page.query_selector('input[name="username"]'):
                    success = True
                    break
            
            if success:
                print("✅ 成功穿透 Cloudflare，正在填写登录信息...")
                await page.fill('input[name="username"]', USERNAME)
                await page.fill('input[name="password"]', PASSWORD)
                
                # 提交登录并等待跳转
                await page.click('input[type="submit"], button[type="submit"]')
                await page.wait_for_load_state("networkidle")
                print("✅ 登录动作已完成。")

                # 2. 跳转签到页
                await page.goto(f"{BASE_URL}/clientarea.php", wait_until="networkidle")
                content = await page.content()
                
                if "您今天已经签到过了" in content:
                    print("✨ 结果：今日已完成签到。")
                else:
                    print("🎯 正在寻找签到按钮...")
                    await page.goto(f"{BASE_URL}/clientarea.php?action=checkin")
                    print("✅ 已尝试通过 Action 路径触发签到。")
            else:
                print("❌ 依然停留在验证页，尝试截取错误图以供分析...")
                # 截图会保存为工作目录下的 error.png
                await page.screenshot(path="error.png")
                print("💡 建议：如果持续失败，可能需要检查账号是否被面板暂时锁定。")

        except Exception as e:
            print(f"⚠️ 运行异常: {str(e)}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
