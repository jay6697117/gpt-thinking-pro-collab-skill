# 2026-09-28 实施验收

本轮已完成授权范围内的本地实现与验证。保留唯一 `GPT-6 Astra Pro` 目标、`GPT-6 Pro` / `6 Pro` 两个别名、显式调用及禁止自动降级；未提交、推送、发布或更改用户全局 Skill。

## 按实施顺序落地

| 批次 | 实施结果 | 主要位置 |
| --- | --- | --- |
| 1–5：执行契约与验证 | 浏览器按宿主能力发现；任务类型与模式分离；补发送确认、恢复和完成判据；明确作者自查与独立审查边界；增加可执行测试与独立场景评估 | [Skill 入口](../../skills/gpt-thinking-pro-collab/SKILL.md)、[浏览器流程](../../skills/gpt-thinking-pro-collab/references/browser-workflow.md)、[审查协议](../../skills/gpt-thinking-pro-collab/references/review-delivery.md)、[场景输入](../../tests/scenarios/cases.json) |
| 6–10、13：使用体验 | README 建立快速开始、故障、更新与加载位置自检；精简入口并按需读取引用；增加归档、基线与交付助手；分开三类报告；修正模板残留检查范围 | [README](../../README.md)、[上下文规则](../../skills/gpt-thinking-pro-collab/references/context.md)、[报告格式](../../skills/gpt-thinking-pro-collab/references/reporting.md)、[统一检查](../../scripts/check.py) |
| 11、12、14：分发与持续验证 | 唯一嵌套安装目录；12 文件白名单；历史记录原样归档；确定性打包；锁定开发依赖；CI；源码、安装、GitHub 与公开目录内容比较 | [包清单](../../package-files.json)、[CI](../../.github/workflows/check.yml)、[分发校验](../../scripts/verify_distribution.py)、[维护指南](../maintenance.md) |

README 从 446 行调整为 168 行，Skill 入口从 180 行调整为 52 行；详细约束保存在引用文件中。旧规划、发现与操作记录的 987 行完整保留在 [历史目录](../history/2026-09-28-before-audit/)，不进入安装包。

## 实际验证

| 检查 | 结果及覆盖 |
| --- | --- |
| Python 3.13.3 | 统一入口通过，49 项测试通过 |
| Python 3.10.21 | 最低支持版本统一入口通过，同样 49 项测试通过 |
| Python 3.14.0 | 本机 uv 默认运行时统一入口通过，同样 49 项测试通过 |
| 结构与文档 | Skill / YAML、模型白名单、显式调用、引用、包清单、模板残留检查通过 |
| 代码规范 | Ruff lint、格式检查、`git diff --check` 通过 |
| 官方 Skill 校验 | skill-creator 的 `quick_validate.py` 返回 `Skill is valid!` |
| 独立场景 | 32 个合成场景完成独立判断，最终比较 0 项不一致 |
| 真实隔离安装 | Skills CLI 1.7.0 在临时目录发现并复制 1 个 Skill，12 个文件逐字节匹配源码；两个已安装助手的 `--help` 成功 |
| 打包 | 白名单 ZIP 的文件集合和内容与源码一致；连续生成相同结果，重复操作幂等 |
| 历史保留 | 三份归档文件与起始 HEAD 中的原文件逐字节一致 |

执行入口：

```bash
uv run --no-project --with-requirements requirements-dev.txt python -B scripts/check.py
uv run --no-project --python 3.13 --with-requirements requirements-dev.txt python -B scripts/check.py
uv run --no-project --python 3.10 --with-requirements requirements-dev.txt python -B scripts/check.py
python3 -B scripts/check_scenario_results.py docs/validation/2026-09-28-scenarios.json
```

工具测试覆盖确定性归档、凭据排除、秘密扫描失败不写出、路径与符号链接拒绝、重复 / 大小写冲突、空项目与未提交 Git 仓库、交付哈希、原始脏文件基线、HEAD 漂移、重叠改动、新增冲突、补丁真实适用性、ZIP 展开上限及“不自动应用 / 不豁免语义审查”。分发测试覆盖缺失、额外和变化文件、固定 GitHub 版本、拒绝不完整目录树。

最终复查增加了 4 项测试并补齐对应边界：远端完整文件发现与异常树处理，以及新增文件 / 目录冲突与 ZIP 目录项冲突。ZIP 负例在修复前实际失败，修复后全部通过。

## 独立评估的证据与校正

评估者只获得当前 Skill、引用、动作定义和场景输入，未获得期望答案或此前实现结论；未操作真实账号。原始最终结果保存在 [场景输出](2026-09-28-scenarios.json)，输入哈希与结果摘要保存在 [机器可读记录](2026-09-28-results.json)。

初轮发现两条期望设置错误，按用户任务语义修正，并对 C01、C21、C30 作独立定向复核：

- C01：`delegate + audit` 仍需目标模型主写审计；只读限制禁止应用代码，不取消外部审计职责。
- C30：用户只要求本地修复，模型额外建议的生产迁移不能扩大任务或制造新的审批要求；补明本地验证已通过的观察后，应报告本地结果。

没有修改评估者的正确结论来迎合原期望。32 个场景属于声明式流程推演，真实浏览器交互另行验收。

## 内容身份

- 技能文件指纹：`9651e487820e2c39fe2aab680ba23e76bd54b9308d36e34520a8f564e774b241`
- 安装包 SHA-256：`44442606f37665b3585667537e53c43ed0483f4ffc245249933552e45e1d1c13`

逐文件 SHA-256、隔离安装路径、场景输入指纹、外部差异和历史文件校验见机器可读记录。

## 已确认的外部状态与限制

- GitHub `main` 尚无新的嵌套发布目录，内容比较返回不一致；本轮未执行提交或推送。
- 本轮期间，[skills.sh 页面](https://skills.sh/jay6697117/gpt-thinking-pro-collab-skill/gpt-thinking-pro-collab)和下载快照已能观察到当前模型名；下载内容仍采用原来的 8 文件结构。相对本轮未发布版本，缺少 10 个新资源、额外包含 6 个仓库维护文件、2 个共同文件内容不同，因此检测器仍返回非零。未主动触发重索引或写入[原上游事项](https://github.com/vercel-labs/skills/issues/2321)；后续发布后需重新比较实际内容。
- CI 已配置 push / PR / 手动触发，以及 Python 3.10 / 3.13 检查；远端 GitHub Actions 尚未执行。
- 未执行真实 ChatGPT 账号 E2E，没有发送任务、上传源码、切换账户或消费目标模型调用。
