# 2026-09-28 skills.sh 发布记录

**状态：GitHub 当前版本已发布并可安装，skills.sh 快照同步尚未完成。**

目标为现有的 [gpt-thinking-pro-collab 页面](https://skills.sh/jay6697117/gpt-thinking-pro-collab-skill/gpt-thinking-pro-collab)，保持原仓库、技能名称、模型白名单、显式调用和禁止自动降级约束。完整发布必须证明该页面和下载快照已使用当前 12 文件版本。

## 已完成的发布步骤

1. 核对现有提交 [b7834df](https://github.com/jay6697117/gpt-thinking-pro-collab-skill/commit/b7834df7f19d2cd2a0ccff2c13bf4df2386b23e2) 已在公开 `main`，12 个运行文件与此前验收版本逐字节一致。
2. 核对 [GitHub Actions 36396585943](https://github.com/jay6697117/gpt-thinking-pro-collab-skill/actions/runs/36396585943) 完成且通过，Python 3.10 / 3.13 两个本地检查作业均成功。该 push 运行按设计跳过了目录核查作业，没有把它称为目录发布通过。
3. 2026-09-28 08:21 UTC 使用官方 Skills CLI 1.7.0，从公开仓库进行一次项目级复制安装；发现 1 个技能，12 个安装文件与本地源码完全匹配。未修改全局 Skill、`HOME` 或 `CODEX_HOME`。
4. 通过只记录公开端点、状态码和 Skill 路径的观察器，确认真实 CLI 的 audit 与 install 请求均返回 200；install 事件使用 `skills/gpt-thinking-pro-collab/SKILL.md`。没有另造安装请求或修改 CLI 行为。

此流程依据 [skills.sh 官方 FAQ](https://www.skills.sh/docs/faq)：技能托管在 GitHub，通过实际 CLI 安装及匿名遥测自动进入目录。

## 尚未通过的端到端核查

| 对比对象 | 当前结果 |
| --- | --- |
| 本地源码与公开 GitHub 提交 | 12 文件全部一致 |
| 本地源码与实际 CLI 安装 | 12 文件全部一致 |
| 本地源码与 skills.sh 下载快照 | 不一致，服务端仍返回原 8 文件结构 |
| 公开页面内容 | 首屏仍为旧“GPT 模型协作 / 解析调用”章节 |

下载快照缺少 10 个新资源，额外包含 6 个仓库维护文件，共同的 SKILL 与元数据 2 个文件内容也不同。2026-09-28 08:30 UTC 的独立查询参数和 no-cache 请求得到 `x-vercel-cache: MISS`、`age: 0`，依然返回同一旧集合，说明最新服务端响应仍未提供目标版本。

当前技能文件指纹为 `9651e487820e2c39fe2aab680ba23e76bd54b9308d36e34520a8f564e774b241`；按同一算法计算的旧目录快照指纹为 `fc0e256d3ef7c8e46abb8ab368a13d50ca1ecf4664d1595f1f5c5813b66b41cf`。详细请求时间、哈希和差异见[机器可读发布证据](2026-09-28-publication.json)。

内置浏览器未提供可用实例，Chrome 工具启动因宿主缺少 app-server 失败；因此公开页面使用其 HTTP 返回的 HTML 核对，没有声称完成交互式浏览器验收。

## 剩余依赖与复核

现有[重索引事项 #2321](https://github.com/vercel-labs/skills/issues/2321)仍开放、无回复；上游 [#780](https://github.com/vercel-labs/skills/issues/780) 和 [#1863](https://github.com/vercel-labs/skills/issues/1863) 记录了同类问题。当前官方文档没有仓库所有者自助重索引入口。本轮未新建或回复第三方 issue，也未尝试受保护的内部接口。

公开快照更新后重新执行：

```bash
python3 -B scripts/verify_distribution.py --github-ref main --catalog
```

还应核对公开页面已出现当前独有的“GPT-6 Astra Pro 协作”标题和“先确定任务合同”章节。只有完整文件集合、逐文件内容和当前页面都一致时，才将发布目标标记完成；安装遥测 200 不是该完成证据。
