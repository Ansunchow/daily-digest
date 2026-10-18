# -*- coding: utf-8 -*-
"""云端「一周食材采购清单」推送（按术后天数动态分期，一次买齐）。周日 18:00(北京) 触发。

术后饮食分期（与每日要闻速报一致）：
  · 术后第 1 周（第 1–7 天）：低脂半流食期
  · 术后第 2–4 周（第 8–28 天）：低脂软食期
  · 术后满 4 周（第 29 天起）：普食过渡期（一般低脂）
手术日期以此推算；如复查/换年后阶段变更，改下方 SURGERY_DATE 即可。
"""
import os
import json
import datetime
import urllib.request

LOCAL_TOKEN = r"D:/workhome/2026-10-03-08-41-34/pushplus_token.txt"

# 胆囊切除术手术日期（术后天数推算基准）
SURGERY_DATE = datetime.date(2026, 10, 13)


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


def post_op_day(today):
    """术后第几天（手术当天记为 0）。"""
    return (today - SURGERY_DATE).days


def stage_info(today):
    d = post_op_day(today)
    if d < 7:
        return 1, d, "术后第1周 · 低脂半流食期"
    elif d < 28:
        return 2, d, "术后第2–4周 · 低脂软食期"
    else:
        return 3, d, "术后满4周 · 普食过渡期（一般低脂）"


# 各阶段食材清单（HTML 片段）
STAGE_BLOCKS = {
    1: """
<h3>🥣 半流食主食</h3>
大米 500g｜小米 300g｜藕粉 1罐｜龙须面/细面条 1束（米汤用大米即可）
<h3>🥚 蛋白（只取蛋清）</h3>
鸡蛋 1托（<b>只吃蛋清、不吃蛋黄</b>）｜嫩豆腐/内酯豆腐 4盒｜鲈鱼 2条 / 龙利鱼 1份 / 鳕鱼 1份（去刺剁茸）｜豆腐脑（可选）
<h3>🥕 蔬果（煮烂 / 做泥）</h3>
胡萝卜 4根｜南瓜 1个(约1kg)｜冬瓜 1块(约500g)｜丝瓜 2根｜山药 300g｜常温苹果 3个（去皮做泥）
<h3>🍵 茶饮</h3>
陈皮 1小包｜菊花(胎菊/白菊)1罐｜麦冬 1包｜枸杞 1包
<h3>🥛 其他</h3>
无糖酸奶 1盒（少量，视耐受）｜生抽｜盐｜植物油（极少，初期尽量不用，全天 &lt;10g）
<hr>
<p><b>本周严格忌口</b>：蛋黄 / 肥肉 / 动物油 / 内脏 / 油炸 / 坚果 / 粗纤维（西兰花·菠菜·木耳·海带·糙米·燕麦·杂粮·生菜凉拌）/ 辛辣酒生冷。<b>每餐 7 分饱，少量多餐（5–6 餐）</b>，细嚼慢咽，餐后静坐 15–20 分钟。</p>
""",
    2: """
<h3>🍚 主食</h3>
大米｜小米｜软米饭用米｜燕麦(煮烂)｜山药 500g｜南瓜 1个｜荞麦面 1束(少量)
<h3>🥚 蛋白</h3>
鸡蛋 1托（<b>蛋黄从 1/4 个试起，耐受再加</b>）｜嫩豆腐 4盒｜鲈鱼 2条 / 鳕鱼 1份｜鸡胸肉 300g(剁茸/切丝)｜去皮鸡腿 2个｜虾 300g(少量)｜瘦肉(去脂)200g
<h3>🥬 蔬果（煮软）</h3>
胡萝卜 4根｜冬瓜｜丝瓜｜西兰花(煮软,少量)｜番茄 3个｜白菜/娃娃菜 各1把｜苹果/梨 各2个(去皮)
<h3>🍄 菌菇</h3>
香菇 200g｜金针菇 2包
<h3>🍵 茶饮</h3>
陈皮 1小包｜菊花(胎菊/白菊)1罐｜麦冬 1包｜枸杞 1包
<h3>🥛 其他</h3>
无糖酸奶 1盒｜生抽｜盐｜植物油（少量，逐步到 20–25ml/天）
<hr>
<p><b>本周注意</b>：仍忌油炸 / 肥肉 / 内脏 / 辛辣 / 酒；蛋黄从少到多试；逐渐从 5–6 餐向 3 餐过渡，避免暴饮暴食；少油烹饪、蒸煮炖焯为主。</p>
""",
    3: """
<h3>🌾 主食</h3>
大米｜小米｜燕麦｜杂粮(适量)｜山药｜南瓜｜荞麦面
<h3>🥚 蛋白</h3>
鸡蛋｜鱼｜鸡胸肉｜虾｜瘦肉(去脂)｜豆制品（豆腐/豆浆）
<h3>🥬 蔬果</h3>
多样化，多蔬菜全谷，优选叶菜 / 瓜茄 / 菌菇
<h3>🍵 茶饮</h3>
陈皮 1小包｜菊花(胎菊/白菊)1罐｜麦冬 1包｜枸杞 1包
<h3>🥛 其他</h3>
无糖酸奶 1盒｜生抽｜盐｜植物油（正常少量）
<hr>
<p><b>长期原则</b>：维持一般低脂饮食——少油炸、少肥肉内脏、优选鱼禽瘦肉与豆制品、多蔬菜全谷；避免暴饮暴食；留意腹泻/脂泻，必要时咨询医生补充脂溶性维生素。</p>
""",
}

# 各阶段开头说明
STAGE_INTRO = {
    1: "术后第 1 周以<b>低脂半流食</b>为主：米粥/烂面/藕粉/米汤、蒸蛋清、嫩豆腐、鱼肉茸、煮烂蔬菜泥。忌蛋黄、忌粗纤维与高脂。",
    2: "术后第 2–4 周逐步从半流食过渡到<b>低脂软食</b>：加软米饭、清蒸鱼、鸡胸肉茸、少油炒软菜，蛋黄从 1/4 个试起（耐受再加）。仍少油、少量多餐。",
    3: "术后满 4 周，遵医嘱过渡到<b>普食</b>，维持一般低脂饮食。",
}

# 通用底部（采购贴士 + 就医提示）
FOOTER = """
<hr>
<p><b>采购小贴士</b>：叶菜分两次买更新鲜；豆腐/鱼/虾尽量当天或次日吃；干货(银耳/木耳/海带/杂粮/茶饮)可一次囤。植物油按阶段少量即可，不必多买。</p>
<p>⚠️ <b>就医提示</b>：体温 &gt;38℃、切口红肿渗液、持续/加重腹痛、频繁呕吐、皮肤或眼白发黄（黄疸）、大便呈陶土色 → 及时联系手术医生。</p>
<p><i>本清单为通用术后参考，非医疗处方，以主管医生的个体化医嘱为准。</i></p>
"""


def build_content(today):
    stage, day, stage_name = stage_info(today)
    stage2_start = (SURGERY_DATE + datetime.timedelta(days=7)).isoformat()
    stage3_start = (SURGERY_DATE + datetime.timedelta(days=28)).isoformat()
    if stage == 1:
        outlook = (
            f"<p><b>后续阶段预告</b>：第 2–4 周（约 {stage2_start} 起）低脂软食期，可逐步加软米饭/清蒸鱼/"
            f"鸡胸肉茸/少量蛋黄；满 4 周（约 {stage3_start} 起）普食过渡，维持一般低脂。</p>"
        )
    elif stage == 2:
        outlook = (
            f"<p><b>后续阶段预告</b>：满 4 周（约 {stage3_start} 起）普食过渡，维持一般低脂。</p>"
        )
    else:
        outlook = (
            f"<p><b>当前阶段</b>：已进入普食过渡期，按上方「长期原则」维持一般低脂即可。</p>"
        )
    return (
        f"<h2>一周食材采购清单 · {stage_name}</h2>"
        f"<p>手术日期：{SURGERY_DATE.isoformat()} ｜ 今天：{today.isoformat()} ｜ "
        f"<b>术后第 {day} 天</b> ｜ 当前阶段：{stage_name}。分量按 <b>1 人 / 1 周</b> 估算。</p>"
        f"<p>{STAGE_INTRO[stage]}</p>"
        f"<hr>{STAGE_BLOCKS[stage]}"
        f"{outlook}"
        f"{FOOTER}"
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
    stage, day, stage_name = stage_info(today)
    title = f"一周食材采购清单 · {stage_name}（术后第{day}天 · 7天不重样）"
    content = build_content(today)
    push(title, content)


if __name__ == "__main__":
    main()
