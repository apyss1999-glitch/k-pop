/**
 * sw.js — K-Pop 韓國女團推薦指南 PWA 的 Service Worker
 *
 * 策略：
 * 1. App Shell（index.html、manifest.json、icons）：
 *    採用 Cache First — 安裝時預先快取，之後直接從快取讀取，離線也能開啟。
 * 2. 外部資源（如 Tailwind CDN、Spotify 連結等第三方網址）：
 *    採用 Network First — 有網路時抓最新版本並更新快取，離線時退而使用快取版本。
 * 3. 版面導覽（如直接輸入網址、重新整理）：
 *    離線時退回快取中的 index.html，確保 App 仍可開啟。
 *
 * 每次更改 App Shell 內容後，請更新下面的 CACHE_VERSION，
 * 讓使用者的瀏覽器知道要清除舊快取、套用新版本。
 */

const CACHE_VERSION = "v1";
const CACHE_NAME = `kpop-guide-cache-${CACHE_VERSION}`;

// 需要預先快取的核心檔案（App Shell）
const APP_SHELL_FILES = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icons/icon-16.png",
  "./icons/icon-32.png",
  "./icons/icon-72.png",
  "./icons/icon-96.png",
  "./icons/icon-128.png",
  "./icons/icon-144.png",
  "./icons/icon-152.png",
  "./icons/icon-180.png",
  "./icons/icon-192.png",
  "./icons/icon-384.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-192.png",
  "./icons/icon-maskable-512.png",
];

// 安裝階段：預先快取 App Shell
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL_FILES))
      .then(() => self.skipWaiting())
  );
});

// 啟用階段：清除舊版本的快取
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith("kpop-guide-cache-") && key !== CACHE_NAME)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

// 攔截請求
self.addEventListener("fetch", (event) => {
  const { request } = event;

  // 只處理 GET 請求，其他方法（POST 等）直接放行
  if (request.method !== "GET") {
    return;
  }

  const url = new URL(request.url);
  const isSameOrigin = url.origin === self.location.origin;

  if (isSameOrigin) {
    // App Shell 自身資源：Cache First
    event.respondWith(cacheFirst(request));
  } else {
    // 第三方資源（Tailwind CDN 等）：Network First
    event.respondWith(networkFirst(request));
  }
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    // 導覽請求離線時，退回快取中的 index.html
    if (request.mode === "navigate") {
      const fallback = await caches.match("./index.html");
      if (fallback) return fallback;
    }
    throw err;
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    throw err;
  }
}
