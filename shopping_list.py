# -*- coding: utf-8 -*-
"""云端「一周食材采购清单」推送（对应每日固定周菜单，一次买齐）。周日 18:00(北京) 触发。"""
import os
import json
import urllib.request

LOCAL_TOKEN = r"D:/workhome/2026-10-03-08-41-34/pushplus_token.txt"


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


CONTENT = """
<h2>一周食材采购清单（术前·胆结石调养）</h2>
<p>对应每日推送的 7 天不重样菜单，一次买齐照着做。分量按 <b>1 人 / 1 周</b> 估算；少油烹饪、蒸煮炖焯为主，严格低脂。</p>
<hr>
<h3>🥬 蔬菜（每天换样）</h3>
秋葵 1把(约200g)｜西兰花 2个｜胡萝卜 4根｜冬瓜 1块(约500g)｜菜心/生菜/娃娃菜 各1把(共约600g)｜黄瓜 2根｜茄子 2根｜菠菜 1把｜苦瓜 1根｜莲藕 1节(约300g)｜番茄 3个｜西葫芦 2根｜芦笋 1把(约200g)｜白萝卜 1根｜海带丝(干)1小包｜木耳(干)1小包｜姜/葱 少许
<h3>🍄 菌菇</h3>
香菇 200g｜金针菇 2包｜银耳(干)1朵
<h3>🍠 薯类主食（当季）</h3>
南瓜 1个(约1kg)｜山药 500g｜芋头 400g
<h3>🥚 肉蛋水产</h3>
鸡蛋 1托(10-15个)｜鲈鱼 2条｜龙利鱼 1份｜鳕鱼 1份｜鸡胸肉 300g｜去皮鸡腿 2个｜虾 400g｜带鱼 300g｜嫩豆腐 4盒｜瘦肉(去脂)200g
<h3>🌾 杂粮主食</h3>
小米｜糙米｜燕麦｜荞麦面 1束｜杂粮米/燕麦米｜薏米(少许)｜莲子(干,少许)｜百合(干,少许)｜红枣(少许)
<h3>🍎 水果坚果</h3>
秋梨 3个｜苹果 2个｜柚子 1个(当季)｜核桃 1小包｜南瓜籽 1包｜杏仁(原味)1包
<h3>🍵 茶饮</h3>
陈皮 1小包｜菊花(胎菊/白菊)1罐｜麦冬 1包｜枸杞 1包
<h3>🥛 其他</h3>
无糖酸奶 1盒(常温)｜生抽｜盐｜植物油(少量)
<hr>
<p><b>采购小贴士</b>：叶菜分两次买更新鲜；豆腐/鱼/虾尽量当天或次日吃；干货(银耳/木耳/海带/杂粮/茶饮)可一次囤。术前严格低脂，植物油也少放；具体禁食时长与菜单以主刀医生/医院通知为准。</p>
"""


def push(title, content):
    token = get_token()
    if not token:
        print("NO TOKEN")
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


if __name__ == "__main__":
    push("一周食材采购清单 · 术前胆结石调养（7天不重样）", CONTENT)
