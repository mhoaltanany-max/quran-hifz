"""يجهّز ملفات data/ من المصادر الأصلية (يُشغَّل مرة واحدة عند تحديث المصادر).

الاستعمال:
  python3 tools/prepare_data.py <quran-json/data/tanzil> <tafsir_api/tafsir/ar-tafsir-muyassar> <data-raw/quranpedia>

المصادر:
  - النص القرآني: Tanzil (الرسم العثماني + النص المبسّط للبحث) عبر github.com/risan/quran-json
  - التفسير الميسّر (مجمع الملك فهد): عبر github.com/spa5k/tafsir_api (MIT)
  - أسباب النزول للواحدي: quranpedia.net (data dumps)
"""
import gzip, html, json, re, sys
from pathlib import Path

tanzil, muyassar, qp = map(Path, sys.argv[1:4])
out = Path(__file__).resolve().parent.parent / "data"
out.mkdir(exist_ok=True)

def dump(name, obj):
    (out / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(name, (out / name).stat().st_size)

# ---- النص القرآني ----
u = json.load(open(tanzil / "uthmani.json", encoding="utf-8"))
sc = json.load(open(tanzil / "simple-clean.json", encoding="utf-8"))
ch = json.load(open(tanzil / "chapters.json", encoding="utf-8"))
q, srch = [], []
for s in range(1, 115):
    vs = [v["text"] for v in u[str(s)]]
    ss = [v["text"] for v in sc[str(s)]]
    assert [v["verse"] for v in u[str(s)]] == list(range(1, len(vs) + 1)) and len(ss) == len(vs)
    if s not in (1, 9):  # البسملة تُعرض عنوانًا مستقلًا، لا جزءًا من الآية الأولى
        vs[0] = " ".join(vs[0].split(" ")[4:])
        assert ss[0].startswith("بسم الله الرحمن الرحيم ")
        ss[0] = " ".join(ss[0].split(" ")[4:])
    q.append(vs); srch.append(ss)
assert sum(map(len, q)) == 6236
idx = ch["indexes"]
dump("quran.json", {
    "q": q, "n": [c["name"] for c in ch["chapters"]],
    "t": [1 if c["type"] == "meccan" else 0 for c in ch["chapters"]],
    "p": [[x["sura"], x["aya"]] for x in idx["pages"]],
    "j": [[x["sura"], x["aya"]] for x in idx["juzs"]],
    "b": u["1"][0]["text"],
})
dump("search.json", srch)

# ---- التفسير الميسّر ----
def clean(t):
    t = t.replace("\r", "")
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

passages, amap, intros = [], [], []
pos = {}
for s in range(1, 115):
    d = json.load(open(muyassar / f"{s}.json", encoding="utf-8"))
    assert [a["ayah"] for a in d] == list(range(1, len(q[s - 1]) + 1)), s
    first = d[0]["text"]
    if "[التفسير]" in first:
        intro, body1 = first.split("[التفسير]", 1)
    else:  # سورة المائدة: لا علامة، فالمقدمة هي الفقرات النقطية
        paras = first.split("\n\n")
        last_bullet = max(i for i, p in enumerate(paras) if p.lstrip().startswith("•"))
        intro, body1 = "\n\n".join(paras[: last_bullet + 1]), "\n\n".join(paras[last_bullet + 1 :])
    intros.append(clean(intro))
    for a in d:
        t = a["text"]
        t = clean(body1) if t == first else clean(t.split("[التفسير]", 1)[1] if "[التفسير]" in t else t)
        if t not in pos:
            pos[t] = len(passages); passages.append(t)
        amap.append(pos[t])
assert len(amap) == 6236
dump("tafsir.json", {"p": passages, "a": amap, "i": intros})

# ---- أسباب النزول للواحدي ----
bk = json.load(gzip.open(qp / "asbab-book-2919.json.gz", "rt", encoding="utf-8"))
assert bk["book"]["id"] == 2919
def asbab_text(h):
    h = re.sub(r"<br\s*/?>", "\n", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h).replace("\r", "")
    h = re.sub(r"[ \t]+\n", "\n", h)
    h = re.sub(r"\n{2,}", "\n", h)
    return h.strip()
CUM = [0]
for s in q: CUM.append(CUM[-1] + len(s))
ap, apos, amap2 = [], {}, {}
for a in bk["ayahs"]:
    t = asbab_text(a["content"][0]["text"])
    if t not in apos:
        apos[t] = len(ap); ap.append(t)
    amap2[CUM[a["surah"] - 1] + a["ayah"] - 1] = apos[t]
dump("asbab.json", {"p": ap, "a": amap2, "version": bk["license"]["version"]})
