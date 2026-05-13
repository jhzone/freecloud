import fetch from "node-fetch";

// ✅ 必须环境变量
const requiredEnv = {
  FC_USERNAME: process.env.FC_USERNAME,
  FC_PASSWORD: process.env.FC_PASSWORD,
  FC_MACHINE_ID: process.env.FC_MACHINE_ID
};

// ✅ 可选环境变量
const optionalEnv = {
  TG_BOT_TOKEN: process.env.TG_BOT_TOKEN,
  TG_CHAT_ID: process.env.TG_CHAT_ID
};

const missingVars = Object.entries(requiredEnv)
  .filter(([_, value]) => !value)
  .map(([key]) => key);

if (missingVars.length) {
  console.error(`❌ 缺少环境变量: ${missingVars.join(", ")}`);
  process.exit(1);
}

const { FC_USERNAME, FC_PASSWORD, FC_MACHINE_ID } = requiredEnv;
const { TG_BOT_TOKEN, TG_CHAT_ID } = optionalEnv;

// ✅ 可扩展的接口配置
const apiEndpoints = [
  "https://raspy-disk-b126.dj2cubz.workers.dev/",
  "https://round-breeze-41c8.dj2cubz.workers.dev/"
];

const getRandomEndpoint = () => apiEndpoints[Math.floor(Math.random() * apiEndpoints.length)];

/**
 * 推送 Telegram 消息
 * @param {string} message
 */
async function sendTelegramMessage(message) {
  if (!TG_BOT_TOKEN || !TG_CHAT_ID) {
    console.warn("⚠️ 未配置 Telegram 推送信息");
    return;
  }

  try {
    const response = await fetch(`https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: TG_CHAT_ID,
        text: message,
        parse_mode: "Markdown"
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.warn(`⚠️ Telegram 推送失败: ${errorText}`);
    } else {
      console.log("✅ Telegram 消息已成功发送");
    }
  } catch (err) {
    console.error("❌ Telegram 推送异常:", err);
  }
}

/**
 * 执行远程接口请求
 */
async function callRemoteAPI() {
  const payload = {
    username: FC_USERNAME,
    password: FC_PASSWORD,
    port: FC_MACHINE_ID
  };

  const endpoint = getRandomEndpoint();
  console.log(`📡 请求接口: ${endpoint}`);

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const responseText = await response.text();
    console.log(`🔁 返回状态码: ${response.status}`);

    try {
      const json = JSON.parse(responseText);
      const message = json?.message || "⚠️ 未包含 message 字段";

      console.log("📬 接口返回:", message);
      await sendTelegramMessage(message);

      if (
        message.includes("请求体不是有效的 JSON") ||
        message.includes("缺少用户名、密码或端口号")
      ) {
        process.exit(1);
      }
    } catch (parseError) {
      console.warn("⚠️ 返回内容非 JSON：", responseText);
      await sendTelegramMessage(`⚠️ 返回非 JSON:\n${responseText}`);
    }
  } catch (err) {
    console.error("❌ 请求失败:", err);
    await sendTelegramMessage(`❌ 请求异常:\n${err.message}`);
    process.exit(1);
  }
}

(async () => {
  console.log("🚀 开始执行任务...");
  await callRemoteAPI();
})();
