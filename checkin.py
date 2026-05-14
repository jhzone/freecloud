import os
import asyncio
from playwright.async_api import async_playwright

# 从 GitHub Secrets 中读取配置
USERNAME = os.environ.get('FREECLOUD_USER')
PASSWORD = os.environ.get('FREECLOUD_PASS')
BASE_URL = "https://panel.freecloud.ltd"

async def run():
    async with async_playwright() as p:
        # 启动浏览器，增加反爬指纹模拟
        browser = p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        print("正在打开页面并等待 Cloudflare 验证...")
        try:
            # 1. 访问首页，等待 CF 验证通过（通常需要 5-10 秒）
            await page.goto(f"{BASE_URL}/login", wait_until="networkidle")
            await asyncio.sleep(8) # 给 CF 盾留出足够的加载时间

            # 2. 检查是否进入了登录页面
            if await page.query_selector('input[name="username"]'):
                print("✅ 已绕过验证，正在登录...")
                await page.fill('input[name="username"]', USERNAME)
                await page.fill('input[name="password"]', PASSWORD)
                
                # 点击登录按钮（根据 WHMCS 结构，通常是 id="login" 或 type="submit"）
                await page.click('input[type="submit"], button[type="submit"]')
                await page.wait_for_load_state("networkidle")
            else:
                print("❌ 未能进入登录页面，可能被 CF 强力拦截。")
                await browser.close()
                return

            # 3. 登录成功后跳转到签到逻辑
            print("正在检查签到状态...")
            await page.goto(f"{BASE_URL}/clientarea.php", wait_until="networkidle")
            
            content = await page.content()
            if "您今天已经签到过了" in content:
                print("✨ 确认结果：今日已完成签到。")
            else:
                print("🎯 正在执行签到点击...")
                # 尝试点击签到按钮（这里使用了常见的签到按钮文字匹配）
                checkin_btn = await page.get_by_text("签到", exact=False)
                if await checkin_btn.is_visible():
                    await checkin_btn.click()
                    await asyncio.sleep(3)
                    print("✅ 签到动作已触发")
                else:
                    # 如果找不到按钮，尝试访问已知的 Action URL
                    await page.goto(f"{BASE_URL}/clientarea.php?action=checkin")
                    print("✅ 已尝试通过 URL 触发签到")

            # 4. 最终检查余额
            await page.goto(f"{BASE_URL}/clientarea.php", wait_until="networkidle")
            final_content = await page.content()
            print("任务完成，请在日志中确认状态。")

        except Exception as e:
            print(f"⚠️ 运行出错: {str(e)}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
