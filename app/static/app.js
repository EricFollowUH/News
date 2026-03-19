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

async function getJson(url) {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload?.message || `Request failed: ${response.status}`);
  }
  return payload;
}

function buildStatusUrl(generateEndpoint, statusPath) {
  if (statusPath.startsWith("http")) {
    return statusPath;
  }
  const endpointUrl = new URL(generateEndpoint, window.location.origin);
  return new URL(statusPath, endpointUrl.origin).toString();
}

async function waitForGeneration(statusUrl) {
  while (true) {
    const data = await getJson(statusUrl);
    if (data.status === "completed") {
      return data;
    }
    if (data.status === "failed") {
      throw new Error(data.message || "生成失败，请稍后再试。");
    }
    generateStatus.textContent = data.message || "正在生成中，请稍候...";
    await new Promise((resolve) => window.setTimeout(resolve, 4000));
  }
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
      if (data.job_id && data.status_url) {
        generateStatus.textContent = data.message || "任务已提交，正在后台生成...";
        const finalData = await waitForGeneration(buildStatusUrl(endpoint, data.status_url));
        generateStatus.innerHTML = `生成完成，<a href="${finalData.article_url}">点击查看最新文章</a>。`;
        window.location.href = finalData.article_url;
        return;
      }
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
