# 每日要闻速报 · 云端版（GitHub Actions）

把「每日 AI + 智能网络物流要闻 + 术前饮食推荐」和「每周采购清单」搬到 GitHub Actions，
**不依赖本机电脑**——出差/关机也照推。

## 包含
- `digest.py`：每日速报生成器（新闻 RSS 聚合 + 饮食按星期几确定性生成 + PushPlus 推送）
- `shopping_list.py`：每周采购清单推送
- `.github/workflows/daily.yml`：每天 **北京时间 06:30** 触发
- `.github/workflows/weekly.yml`：每周日 **北京时间 18:00** 触发

## 部署步骤
1. 在 GitHub 新建一个**空仓库**（如 `daily-digest`）。
2. 把本目录全部内容（含 `.github/`）推到仓库根目录：
   ```bash
   git init
   git add .
   git commit -m "init cloud digest"
   git branch -M main
   git remote add origin https://github.com/<你的用户名>/daily-digest.git
   git push -u origin main
   ```
3. 仓库 **Settings → Secrets and variables → Actions → New repository secret** 添加：
   - `PUSHPLUS_TOKEN`：你的 PushPlus token（必填）
   - `NEWS_API_KEY`（可选）：OpenAI / DeepSeek 等 API Key，用于对 RSS 标题做 ≤40 字精编；
     不填则用原始 RSS 标题（免费、可用）。
   - `NEWS_BASE_URL`（可选）：兼容 OpenAI 的接口地址，如 `https://api.deepseek.com/v1`
   - `NEWS_MODEL`（可选）：模型名，如 `gpt-4o-mini` / `deepseek-chat`
4. **Actions** 页确认工作流已启用。GitHub 免费额度 2000 分钟/月，本任务月耗约 30 分钟。
5. 验证：在 **Actions → 工作流 → Run workflow** 手动跑一次，微信收到即成功。

## 时区说明
GitHub Actions 的 cron 用 **UTC**。代码里已换算：
- 06:30 北京 = 22:30 UTC 前一天 → `30 22 * * *`
- 18:00 北京周日 = 10:00 UTC 周日 → `0 10 * * 0`

## 上线后
云端跑通后，把本机 WorkBuddy 里的本地定时任务「每日AI要闻速报·v1本地版」**暂停**，
避免同一天推两条。本地任务 ID：`8f200714-74fe-4337-ae04-18d54f01369b`。

## 注意
- 新闻经 RSS 聚合，单源挂掉自动跳过，不影响整体。
- 饮食为固定周菜单（术前·胆结石调养），具体术前禁食以医院通知为准。
- PushPlus 需实名认证才能发消息。
