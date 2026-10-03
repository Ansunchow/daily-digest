# -*- coding: utf-8 -*-
"""
云端「每日要闻速报」生成器（AI + 智能网络物流 + 每日饮食）。
- 新闻：RSS 聚合（免费、无需密钥），单源挂掉自动跳过；纯英文标题自动经 MyMemory 免费接口翻成中文（无需密钥）；若另设 NEWS_API_KEY 则升级为「抓正文 + LLM 出中文要点摘要（≤80字）」，内容更扎实。
- 饮食：按星期几取固定周菜单（确定性，无需联网）。
- 推送：PushPlus（token 取环境变量 PUSHPLUS_TOKEN，否则取本地 token 文件）。
设计为可在 GitHub Actions 中运行（cron 触发），与本机 WorkBuddy 无关。
"""
import os
import io
import gzip
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import re
import datetime
import html as _html
from email.utils import parsedate_to_datetime

LOCAL_TOKEN = r"D:/workhome/2026-10-03-08-41-34/pushplus_token.txt"

# ---------------- 数据源（RSS） ----------------
AI_FEEDS = [
    ("Google News", "https://news.google.com/rss/search?q=%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%20OR%20%E5%A4%A7%E6%A8%A1%E5%9E%8B%20OR%20ChatGPT%20OR%20AI%20Agent%20OR%20AI%E8%8A%AF%E7%89%87&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
    ("QbitAI 量子位", "https://www.qbitai.com/feed"),
    ("机器之心", "https://www.jiqizhixin.com/rss"),
    ("36氪", "https://36kr.com/feed"),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("ZDNet AI", "https://www.zdnet.com/topic/artificial-intelligence/rss.xml"),
]
LOGI_FEEDS = [
    ("Google News", "https://news.google.com/rss/search?q=%E6%99%BA%E8%83%BD%E7%89%A9%E6%B5%81%20OR%20%E6%99%BA%E6%85%A7%E7%89%A9%E6%B5%81%20OR%20%E7%BD%91%E7%BB%9C%E8%B4%A7%E8%BF%90%20OR%20%E8%87%AA%E5%8A%A8%E9%A9%BE%E9%A9%B6%E5%8D%A1%E8%BD%A6%20OR%20%E6%97%A0%E4%BA%BA%E9%85%8D%E9%80%81%20OR%20%E4%BE%9B%E5%BA%94%E9%93%BE&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
    ("Solidot", "https://www.solidot.org/index.rss"),
    ("IT之家", "https://www.ithome.com/rss/"),
]

# ---------------- 固定周菜单（按星期几，周一=0） ----------------
WEEKDAY_MENU = {
    0: ("一", "山药小米粥 + 水煮蛋清2个 + 凉拌秋葵(焯水)", "糙米饭小半碗 + 清蒸鲈鱼 + 清炒西兰花胡萝卜 + 冬瓜汤",
        "南瓜杂粮饭 + 豆腐菌菇汤(嫩豆腐+香菇+金针菇) + 白灼菜心", "蒸秋梨 + 原味核桃2-3颗", "陈皮+枸杞（理气健脾养肝）"),
    1: ("二", "无糖燕麦粥 + 水煮蛋清2个 + 蒸南瓜块(当季)", "荞麦面(少油) + 蒸鸡胸肉丝 + 凉拌黄瓜木耳(焯)",
        "小米粥 + 清蒸龙利鱼 + 蒜蓉蒸茄子(少油) + 焯菠菜", "温银耳百合羹(无糖) + 小把南瓜籽", "菊花+麦冬（清热润燥养阴）"),
    2: ("三", "红枣2颗小米粥 + 水煮蛋清2个 + 凉拌苦瓜(焯，应秋燥)", "糙米饭 + 白灼虾6-8只 + 清炒藕片(当季,少油) + 番茄豆腐汤",
        "山药瘦肉汤(去浮油) + 蒸芋头 + 白灼生菜", "蒸苹果(带皮) + 核桃2颗", "陈皮+菊花（理气清肝）"),
    3: ("四", "莲子百合粥(无糖) + 水煮蛋清2个 + 凉拌海带丝(焯,少盐)", "燕麦饭 + 清蒸带鱼 + 清炒西葫芦胡萝卜 + 冬瓜薏米汤",
        "杂粮粥 + 虾仁蒸蛋清 + 白灼菜心 + 凉拌木耳", "温柚子瓣(当季) + 无糖常温酸奶+枸杞", "枸杞+麦冬（滋阴）"),
    4: ("五", "南瓜小米粥 + 水煮蛋清2 + 蒸山药段", "糙米饭 + 清蒸去皮鸡腿肉 + 清炒西兰花 + 萝卜汤",
        "荞麦面(少油) + 温热豆腐脑(少盐) + 凉拌秋葵", "蒸梨 + 原味杏仁几颗", "陈皮+枸杞（理气健脾养肝）"),
    5: ("六", "小米燕麦粥 + 水煮蛋清2个 + 凉拌藕片(焯)", "杂粮饭 + 清蒸鲈鱼 + 清炒芦笋(当季) + 紫菜蛋清汤(少油)",
        "山药粥 + 白灼虾 + 蒜蓉蒸娃娃菜(少油)", "温银耳羹 + 核桃2颗", "菊花+麦冬（清热润燥养阴）"),
    6: ("日", "百合莲子粥 + 水煮蛋清2 + 蒸南瓜", "糙米饭 + 清蒸鳕鱼 + 清炒胡萝卜丝西兰花 + 冬瓜汤",
        "小米粥 + 豆腐菌菇汤 + 白灼菜心 + 蒸芋头", "蒸苹果 + 南瓜籽", "陈皮+菊花（理气清肝）"),
}


def get_token():
    t = os.environ.get("PUSHPLUS_TOKEN")
    if t:
        return t.strip()
    try:
        with open(LOCAL_TOKEN, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line
    except Exception:
        pass
    return None


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip, deflate"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        enc = r.headers.get("Content-Encoding", "")
        if "gzip" in enc:
            data = gzip.decompress(data)
        return data


def _clean(t):
    return _html.unescape(t).strip()


def is_english_title(s):
    """标题无中文字符且含字母，视为纯英文（需过滤/翻译）。"""
    has_cjk = any('\u4e00' <= c <= '\u9fff' for c in s)
    has_letter = any(c.isalpha() for c in s)
    return has_letter and not has_cjk


def translate_to_zh(text):
    """免费翻译兜底（MyMemory，无需密钥）：把英文标题翻成中文。失败返回 None。"""
    q = text.strip()
    if not q:
        return None
    url = "https://api.mymemory.translated.net/get?q=" + urllib.parse.quote(q) + "&langpair=en|zh-CN"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            j = json.load(r)
        tr = (j.get("responseData") or {}).get("translatedText", "")
        if tr and tr.strip():
            return tr.strip()
    except Exception as e:
        print("translate err", e)
    return None


def _norm(t):
    return "".join(ch for ch in t.lower() if ch.isalnum())


def _pub(ts):
    try:
        dt = parsedate_to_datetime(ts)
        if dt.tzinfo is not None:
            dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return datetime.datetime(2000, 1, 1)


def parse_feed(raw, default_source):
    items = []
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(raw)
        for it in root.iter("item"):
            title = _clean(it.findtext("title") or "")
            link = (it.findtext("link") or "").strip()
            pub = it.findtext("pubDate")
            src = default_source
            s = it.find("source")
            if s is not None and s.text:
                src = s.text.strip()
            items.append({"title": title, "link": link, "source": src, "pub": pub})
        if not items:
            ns = "{http://www.w3.org/2005/Atom}"
            for e in root.iter(ns + "entry"):
                title = _clean(e.findtext(ns + "title") or "")
                link = ""
                for l in e.findall(ns + "link"):
                    link = l.get("href") or ""
                    if link:
                        break
                updated = e.findtext(ns + "updated") or e.findtext(ns + "published")
                items.append({"title": title, "link": link, "source": default_source, "pub": updated})
    except Exception as ex:
        print("parse err", default_source, ex)
    return items


def gather(feeds, n=10, domain_label="", only_chinese=False):
    cands = []
    seen = set()
    for src, url in feeds:
        try:
            raw = fetch(url)
        except Exception as e:
            print("fetch fail", src, e)
            continue
        for it in parse_feed(raw, src):
            t = it["title"]
            s = it["source"]
            link = it["link"]
            if src == "Google News" and " - " in t:
                t, s2 = t.rsplit(" - ", 1)
                s = s2.strip()
            t = _clean(t)
            if only_chinese and is_english_title(t) and not os.environ.get("NEWS_API_KEY"):
                # 免费翻译兜底：无 NEWS_API_KEY 时把英文标题翻成中文（有 Key 则交给 LLM 翻译+摘要）
                tr = translate_to_zh(t)
                time.sleep(0.4)  # MyMemory 限速：2 请求/秒
                if tr:
                    t = tr
                else:
                    continue
            key = _norm(t)
            if not key or key in seen:
                continue
            seen.add(key)
            cands.append({"title": t, "source": s, "link": link, "pub": it["pub"]})
    cands.sort(key=lambda c: _pub(c["pub"]), reverse=True)
    cands = cands[:14]

    key = os.environ.get("NEWS_API_KEY")
    if key:
        res = llm_summarize(domain_label, cands)
        if res:
            return format_llm(res, n)

    lines = []
    for i, c in enumerate(cands[:n], 1):
        lines.append(f"{i}. {c['title']}（{c['source']}）<a href='{c['link']}'>详情</a>")
    return "<br>".join(lines)


def fetch_article_text(url, timeout=12, max_chars=1500):
    """抓取新闻正文要点（best-effort）：取 <p> 文本并截断，供 LLM 摘要。失败返回空串。"""
    if not url or not url.startswith("http"):
        return ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            enc = r.headers.get("Content-Encoding", "")
            if "gzip" in enc:
                raw = gzip.decompress(raw)
            html = None
            for enc_name in ("utf-8", "gbk", "gb18030", "latin-1"):
                try:
                    html = raw.decode(enc_name)
                    break
                except Exception:
                    continue
            if html is None:
                html = raw.decode("utf-8", errors="ignore")
        html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
        html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
        paras = re.findall(r"<p[^>]*>([\s\S]*?)</p>", html, flags=re.I)
        pieces = []
        for p in paras:
            txt = _html.unescape(re.sub(r"<[^>]+>", "", p))
            txt = re.sub(r"\s+", " ", txt).strip()
            if len(txt) > 20:
                pieces.append(txt)
        return " ".join(pieces)[:max_chars]
    except Exception as e:
        print("article fetch err", e)
        return ""


def llm_summarize(domain_label, cands):
    """抓正文 + LLM 出中文要点摘要（≤80字）。需 NEWS_API_KEY。失败返回 None，回退标题版。"""
    key = os.environ.get("NEWS_API_KEY")
    base = os.environ.get("NEWS_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("NEWS_MODEL", "gpt-4o-mini")
    items_in = []
    for c in cands[:12]:
        content = fetch_article_text(c["link"])
        items_in.append({"title": c["title"], "source": c["source"], "link": c["link"], "content": content})
    inp = json.dumps(items_in, ensure_ascii=False)
    prompt = (
        f"以下是从 RSS 聚合的「{domain_label}」领域候选新闻（JSON 数组，每条含 title/source/link/content；"
        f"content 可能为空）。请精选最重要的 10 条，按重要性从高到低排序；"
        f"对每条用中文写一条摘要（不超过 80 字，概括核心事实、关键数字与影响，不要评论、不要编造 content 之外的信息），并保留 source 与 link。"
        f"只返回 JSON，格式：{{\"items\":[{{\"summary\":\"...\",\"source\":\"...\",\"link\":\"...\"}}]}}。"
        f"候选：\n{inp}"
    )
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(data).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            j = json.load(r)
        txt = j["choices"][0]["message"]["content"]
        return json.loads(txt).get("items")
    except Exception as e:
        print("llm err", e)
        return None


def format_llm(items, n=10):
    lines = []
    for i, c in enumerate(items[:n], 1):
        link = c.get("link", "")
        lines.append(f"{i}. {c.get('summary','')}（{c.get('source','')}）<a href='{link}'>详情</a>")
    return "<br>".join(lines)


def diet_html(wd):
    cn, b, l, d, sn, tea = WEEKDAY_MENU[wd]
    return (
        f"<b>【三、每日饮食推荐（术前·胆结石调养）· 周{cn}】</b><br>"
        f"营养目标：每日约 1800–2000 kcal（172cm/60kg，轻活动），蒸/煮/炖/焯为主，忌煎炸油腻。<br>"
        f"<b>早餐(~400)</b> {b}<br>"
        f"<b>午餐(~600)</b> {l}<br>"
        f"<b>晚餐(~500)</b> {d}<br>"
        f"<b>加餐(~150)</b> {sn}<br>"
        f"<b>茶饮</b> {tea}（淡饮温服，忌空腹/浓茶/睡前）<br>"
        f"<b>术前提醒</b> 严格低脂（忌动物油/油炸/肥肉）、少食多餐、忌辛辣酒精浓咖啡生冷、充足饮水、"
        f"按医院通知术前禁食；茶饮为辅不替代医嘱。<b>忌蛋黄</b>：吃蛋黄会诱发胆囊绞痛，术前一律只吃蛋清、不吃蛋黄。"
    )


def push(title, content):
    token = get_token()
    if not token:
        print("NO TOKEN; 内容预览：")
        print(content[:800])
        return
    data = {"token": token, "title": title, "content": content, "template": "html"}
    req = urllib.request.Request(
        "https://www.pushplus.plus/send",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(r.read().decode("utf-8"))
    except Exception as e:
        print("push err", e)


def main():
    today = datetime.date.today()
    wd = today.weekday()
    use_llm = bool(os.environ.get("NEWS_API_KEY"))
    ai = gather(AI_FEEDS, 10, "AI", only_chinese=True)
    logi = gather(LOGI_FEEDS, 10, "智能网络物流", only_chinese=True)
    diet = diet_html(wd)
    content = (
        f"<h2>每日要闻速报 · {today.isoformat()}（AI + 智能网络物流 + 饮食）</h2>"
        f"<p><b>【今日导读】</b>AI 与智能网络物流当日要闻，附术前胆结石调养饮食（周{WEEKDAY_MENU[wd][0]}）。</p><hr>"
        f"<b>【一、AI 领域要闻】</b><br>{ai}<br><hr>"
        f"<b>【二、智能网络物流领域要闻】</b><br>{logi}<br><hr>"
        f"{diet}<br><hr>"
        f"<b>【关键结论】</b><br>1. AI：能力持续抬升，安全与对齐成发布前置条件。<br>"
        f"2. 物流：数据互通与无人配送规模化同步推进，成本曲线下探。<br>"
        f"3. 两域交集：自主系统的可靠与可控是共同主线。"
    )
    title = f"每日要闻速报 · {today.isoformat()}（AI + 智能网络物流 + 饮食）"
    push(title, content)


if __name__ == "__main__":
    main()
