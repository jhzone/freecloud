import os
import asyncio
from playwright.async_api import async_playwright

# 从 GitHub Secrets 中读取配置
USERNAME = os.environ.get('FREECLOUD_USER')
PASSWORD = os.environ.get('FREECLOUD_PASS')
BASE_URL = "https://panel.freecloud.ltd"

async def run():
    async with async_playwright() as p:
        # 修正点：这里必须加上 await
        browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        print("正在打开页面并等待 Cloudflare 验证...")
        try:
            # 1. 访问登录页
            await page.goto(f"{BASE_URL}/login", wait_until="networkidle")
            # Cloudflare 通常需要 5-10 秒进行环境检测
            await asyncio.sleep(10) 

            # 2. 检查并登录
            if await page.query_selector('input[name="username"]'):
                print("✅ 已成功绕过 Cloudflare，正在登录...")
                await page.fill('input[name="username"]', USERNAME)
                await page.fill('input[name="password"]', PASSWORD)
                
                # 提交登录
                await page.click('input[type="submit"], button[type="submit"]')
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
            else:
                print("❌ 未能检测到登录表单，可能仍在验证页或被拦截。")
                # 截图保存以便后续排查（如果需要）
                # await page.screenshot(path="error.png")
                await browser.close()
                return

            # 3. 执行签到
            print("正在跳转至会员中心...")
            await page.goto(f"{BASE_URL}/clientarea.php", wait_until="networkidle")
            
            content = await page.content()
            if "您今天已经签到过了" in content:
                print("✨ 确认结果：今日已完成签到。")
            else:
                print("🎯 尝试执行签到点击...")
                # 尝试通过文字内容寻找按钮
                checkin_btn = page.get_by_text("签到", exact=False)
                if await checkin_btn.is_visible():
                    await checkin_btn.click()
                    await asyncio.sleep(3)
                    print("✅ 签到动作已触发。")
                else:
                    # 如果找不到按钮，直接访问签到 API 路径
                    await page.goto(f"{BASE_URL}/clientarea.php?action=checkin")
                    print("✅ 已尝试通过路径触发签到。")

            # 4. 获取最终余额
            final_content = await page.content()
            if "积分" in final_content:
                print("任务执行完毕，请检查账户余额变化。")

        except Exception as e:
            print(f"⚠️ 运行出错: {str(e)}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
