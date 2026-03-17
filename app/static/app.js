async function postForm(url, body) {
  const response = await fetch(url, {
    method: "POST",
    body,
  });
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await response.json() : null;
  if (!response.ok) {
    throw new Error(payload?.message || `Request failed: ${response.status}`);
  }
  return payload;
}

const generateButton = document.querySelector("#generate-button");
const generateStatus = document.querySelector("#generate-status");

if (generateButton) {
  generateButton.addEventListener("click", async () => {
    generateButton.disabled = true;
    generateStatus.textContent = "正在生成文章、播客文稿和音频，请稍候...";
    try {
      const endpoint = generateButton.dataset.endpoint || "/api/generate-now";
      const data = await postForm(endpoint, new FormData());
      generateStatus.innerHTML = `生成完成，<a href="${data.article_url}">点击查看最新文章</a>。`;
      window.location.href = data.article_url;
    } catch (error) {
      generateStatus.textContent = error.message || "生成失败，请检查 Gemini API 配置或稍后再试。";
    } finally {
      generateButton.disabled = false;
    }
  });
}

const subscribeForm = document.querySelector("#subscribe-form");
const subscribeStatus = document.querySelector("#subscribe-status");

if (subscribeForm) {
  subscribeForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    subscribeStatus.textContent = "正在提交订阅...";
    try {
      const data = await postForm("/api/subscribe", new FormData(subscribeForm));
      subscribeStatus.textContent = data.message;
      subscribeForm.reset();
    } catch (error) {
      subscribeStatus.textContent = "订阅失败，请检查邮箱格式或稍后再试。";
    }
  });
}
