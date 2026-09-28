# 现有重索引事项的补充说明草稿

以下正文拟追加到 [vercel-labs/skills#2321](https://github.com/vercel-labs/skills/issues/2321)，尚未发送。

---

补充最新的发布与复核结果，请刷新现有 `jay6697117/gpt-thinking-pro-collab-skill/gpt-thinking-pro-collab` 记录，保留原名称和安装历史。

初始问题中的旧模型快照已有变化，但当前新发布的完整技能包仍未同步：

- 当前公开提交：[`0b644bb`](https://github.com/jay6697117/gpt-thinking-pro-collab-skill/commit/0b644bbd848732c31afbc76467a4c64c16c68109)。
- 当前技能入口：[`skills/gpt-thinking-pro-collab/SKILL.md`](https://github.com/jay6697117/gpt-thinking-pro-collab-skill/blob/0b644bbd848732c31afbc76467a4c64c16c68109/skills/gpt-thinking-pro-collab/SKILL.md)。技能目录已从仓库根迁至该子目录。
- [当前 CI](https://github.com/jay6697117/gpt-thinking-pro-collab-skill/actions/runs/36398126226) 已通过；运行包包含 12 个文件。
- 2026-09-28 08:21 UTC，通过官方 Skills CLI 1.7.0，从公开仓库进行一次启用遥测的隔离安装。12 个安装文件均与源码逐字节一致；install 请求返回 HTTP 200，`skillFiles` 明确包含 `skills/gpt-thinking-pro-collab/SKILL.md`。
- 2026-09-28 08:38 UTC 再次读取[公开下载接口](https://www.skills.sh/api/download/jay6697117/gpt-thinking-pro-collab-skill/gpt-thinking-pro-collab)，仍返回原来的 8 文件结构。
- 此前 08:30 UTC 的 no-cache 独立查询也得到 `x-vercel-cache: MISS`、`age: 0`，但内容仍旧。

当前 `SKILL.md` SHA-256：`d7a3ecc5936ead4c957d60a6e88646e5558712962775d6d083057b91b2d35aa3`。

目录快照中的 `SKILL.md` SHA-256：`d78cf1c4d98ba7f7a62ba0e5b945121e3971544492ae9e0106eccc1ae0b5b51c`。

当前下载缺少以下 10 个运行资源：

- `assets/delivery-manifest.example.json`
- `assets/session.example.json`
- `references/browser-workflow.md`
- `references/configuration.md`
- `references/context.md`
- `references/reporting.md`
- `references/review-delivery.md`
- `scripts/artifact_utils.py`
- `scripts/context_bundle.py`
- `scripts/verify_delivery.py`

同时还夹带原仓库 README、规划和测试等 6 个维护文件，SKILL 和元数据内容也不同。请从当前 `main` 的新技能子目录替换现有文件快照并刷新页面；不需要创建新条目或更改 Skill 名称。

完整的[发布证据](https://github.com/jay6697117/gpt-thinking-pro-collab-skill/blob/0b644bbd848732c31afbc76467a4c64c16c68109/docs/validation/2026-09-28-publication.md)与[机器可读记录](https://github.com/jay6697117/gpt-thinking-pro-collab-skill/blob/0b644bbd848732c31afbc76467a4c64c16c68109/docs/validation/2026-09-28-publication.json)均已公开。
