# 维护与发布验证

## 目录边界

- `skills/gpt-thinking-pro-collab/` 是唯一安装目录；`package-files.json` 明确列出所有运行资源，CI 拒绝遗漏和意外文件。
- `scripts/` 是仓库级检查、打包和分发比对工具，不作为 Skill 的运行依赖。
- `tests/scenarios/` 保存声明式工作流的场景、动作定义与期望；`tests/test_artifacts.py` 等测试实际 Python 工具行为。
- `docs/history/` 保存原任务记录，历史模型配置不代表当前规则。skills.sh 重索引仍作为独立外部事项跟踪。

## 一个检查入口

按 README 安装锁定的开发工具后运行 `python -B scripts/check.py`。CI 在 Python 3.10 与 3.13 上运行相同入口；不要求维护者私有目录中的 skill-creator 或全局 Ruff。

需要单独调试时：

```bash
python3 -B -m unittest discover -s tests -v
python3 -m ruff check .
python3 -m ruff format --check .
```

`check.py` 只检查当前交付文档和运行文件中的模板残留，排除维护脚本自身、测试数据和历史记录，不会匹配它自己展示的搜索命令。官方 skill-creator 校验可作为附加检查，但不替代项目测试。

## 独立场景评估

静态合同只能核查结构与不变量。对配置、权限、发送、恢复、审核责任等流程修改，使用 skill-creator 的独立前向评估方式：给独立评估者当前 SKILL、按需引用、`tests/scenarios/actions.json` 和 `cases.json`，不给期望答案、实现结论或旧报告。只进行合成推演，不操作真实账号或发送消息。

每个场景输出 `id`、`decision`、`reason`，保存 JSON 数组后比较：

```bash
python3 -B scripts/check_scenario_results.py /tmp/independent-results.json
```

不一致时先分析需求和当前规则，不把评估者答案直接写成新期望来制造通过。确认是规则缺陷则修规则并重新评估受影响场景；期望本身错误时记录证据后修正。记录被评估的源文件哈希、场景数、结果和限制。该比较器不会运行模型；CI 的工具测试也不会冒充已执行合成评估。

真实账号 E2E 是另一层验证：需有对应授权、可用内置浏览器和目标档位，才测试选模、发送、等待、取件与本地接入。本轮本地验证不隐含该授权。

## 打包与安装

打包工具只复制白名单中的技能资源，生成可重复 ZIP 和独立 manifest。相同输出幂等，不同已有文件拒绝覆盖。历史记录、测试与仓库 README 不应出现在包或安装目录中。

隔离验证应在临时目录中以项目级、复制模式安装本地技能；不改写 `HOME` / `CODEX_HOME`、不安装到用户全局目录。禁用遥测，确认只发现一个技能，逐文件比较安装结果与白名单，然后从安装目录运行助手的 `--help` 或合成测试。

## 内容一致性

`verify_distribution.py` 默认打印本地文件指纹；可分别比较安装目录、指定公开 GitHub ref 与 skills.sh 快照。比对包含完整文件集合和内容，能识别“SKILL 已更新但 references 遗漏”和旧根目录包夹带维护文件的情况。GitHub ref 先解析到固定 commit，再通过完整文件树发现所有运行资源，避免漏掉额外文件或混用变化中的分支；树被截断或包含非普通文件时失败。[GitHub 文件树接口](https://docs.github.com/en/rest/git/trees#get-a-tree)

目录页面还必须出现当前模型标识，不能只因 HTTP 200 而通过。

发布前本地未提交 / 未推送时，远端不匹配是预期事实，应分别报告。获得提交 / 推送授权后再验证公开 ref；本站过期快照可能仍需上游处理。工具没有发布、刷新目录或发送 issue 的副作用。

GitHub Actions 的 `workflow_dispatch` 可选启用公开目录核查；普通 PR 验证只运行本地检查，避免因尚未发布或上游缓存阻塞代码验证。CI 配置落地不等于已在远端执行，最终交付应区分二者。

本轮实际结果及原始场景输出见 [2026-09-28 实施验收](validation/2026-09-28-implementation.md)。
