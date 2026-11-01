"""يبني index.html (التطبيق كاملًا في ملف واحد) من src/ و data/.

  python3 tools/build.py                 -> index.html
  python3 tools/build.py --body out.html -> نسخة بلا رأس الصفحة (للمعاينة كـ Artifact)
"""
import base64, sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
src, data = root / "src", root / "data"

def js(name):  # JSON آمن داخل وسم <script>
    return (data / name).read_text(encoding="utf-8").replace("</", "<\\/")

body = (src / "app.html").read_text(encoding="utf-8")
font = base64.b64encode((src / "scheherazade-new-regular.woff2").read_bytes()).decode()
for key, val in {"__FONT__": font, "__DATA__": js("quran.json"), "__TAFSIR__": js("tafsir.json"),
                 "__ASBAB__": js("asbab.json"), "__SEARCH__": js("search.json")}.items():
    assert body.count(key) == 1, key
    body = body.replace(key, val)

if len(sys.argv) > 2 and sys.argv[1] == "--body":
    Path(sys.argv[2]).write_text(body, encoding="utf-8")
    sys.exit()

i = body.index('<div id="app"')
page = (
    '<!doctype html>\n<html lang="ar" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    '<meta name="theme-color" content="#1C5A53">\n'
    + (src / "pwa-head.html").read_text(encoding="utf-8")
    + body[:i] + "</head>\n<body>\n" + body[i:]
    + (src / "pwa-tail.html").read_text(encoding="utf-8")
    + "</body>\n</html>\n"
)
(root / "index.html").write_text(page, encoding="utf-8")
print("index.html", len(page.encode()))
