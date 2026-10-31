// رفيق الحفظ: يخزّن التطبيق كاملًا على الجهاز ليعمل بدون إنترنت.
const VERSION = "hifz-v1";
const CORE = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./icon-maskable-512.png", "./apple-touch-icon.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // التلاوات الصوتية لا تُخزَّن (حجمها كبير)، تُطلب من الإنترنت مباشرة.
  if (url.hostname.endsWith("islamic.network")) return;

  // خطوط الواجهة من Google: تُخزَّن عند أول تحميل ثم تعمل بدون إنترنت.
  if (url.hostname.includes("fonts.googleapis.com") || url.hostname.includes("fonts.gstatic.com")) {
    e.respondWith(
      caches.open(VERSION).then((c) =>
        c.match(req).then((hit) => hit || fetch(req).then((res) => { c.put(req, res.clone()); return res; }).catch(() => hit))
      )
    );
    return;
  }

  if (url.origin !== location.origin) return;

  // ملفات التطبيق: من الجهاز أولًا، مع تحديث في الخلفية عند توفر الإنترنت.
  e.respondWith(
    caches.open(VERSION).then((c) =>
      c.match(req, { ignoreSearch: true }).then((hit) => {
        const net = fetch(req).then((res) => { if (res.ok) c.put(req, res.clone()); return res; }).catch(() => null);
        return hit || net.then((r) => r || c.match("./index.html"));
      })
    )
  );
});
