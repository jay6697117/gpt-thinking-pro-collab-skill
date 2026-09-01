# 任务计划：GPT-5.6 Thinking 与可配置模型兼容

## 目标

将当前项目改造为兼容 GPT-5.6 Thinking，并提供一个明确的配置项；运行时必须使用该配置项指定的模型，而不是在业务代码中写死模型。

当前追加目标：仅调整 `README.md` 的“使用”章节，使调用示例的组织与版式对齐参考仓库 `genoooool/gpt-pro-collab-skill` 及用户提供的截图，同时保留本项目的名称、双模型配置和现有运行语义。

当前最新目标：审计并修订 `README.md`，将“使用”区域所有显式 `model` 示例统一为 `GPT-5.6 Pro`，全篇模型说明统一到 `GPT-5.6 Pro` / `GPT-5.6 Sol Pro` 语义，并把除不可翻译标识符外的可读英文说明全部改为简体中文。

## 关键约束

- 保留现有模型的兼容能力，除非当前实现本身与 GPT-5.6 Thinking 的协议要求冲突。
- 模型选择必须有单一、可追踪的配置来源，并贯穿所有真实调用路径。
- 代码、标识符、注释和提交信息使用 English。
- 修改应尽量小且可审阅，不做与模型兼容无关的重构。
- 完成声明必须由源码、测试、构建或可执行验证共同证明。

## 阶段

### Phase 1：恢复上下文并审计当前架构

**Status:** complete

交付物：模型调用链、配置入口、协议约束和现有测试的证据。

### Phase 2：确定兼容方案与配置契约

**Status:** complete

交付物：配置优先级、默认行为、GPT-5.6 Thinking 参数策略。

### Phase 3：实施模型配置和调用链改造

**Status:** complete

交付物：配置读取、类型定义、调用方接线及必要兼容逻辑。

### Phase 4：补充测试与文档

**Status:** complete

交付物：配置覆盖、模型透传、兼容行为和使用说明。

### Phase 5：执行完整验证与完成审计

**Status:** complete

交付物：测试、构建、静态检查、差异检查及逐项验收。

### Phase 6：迁移 README Skill 名称并完成中文化

**Status:** complete

交付物：仅修改 `README.md`，将用户可见的 Skill 名称统一为 `gpt-thinking-pro-collab`，并把仍为英文的使用说明改为简体中文。

### Phase 7：参考上游仓库优化 README

**Status:** complete

交付物：对比参考仓库与本地当前实现，重构 `README.md` 的信息架构、安装与使用说明、行为边界和验证指引，同时保留本项目的新名称与可配置模型语义。

### Phase 8：按参考版式调整 README 使用章节

**Status:** complete

交付物：比对参考仓库当前“使用”章节和用户截图，仅修改本地 `README.md` 对应章节的示例格式，并完成 Markdown、差异与文档合同核验。

### Phase 9：统一 README 默认模型并完成全篇中文化

**Status:** complete

交付物：读取两张新截图，逐项审计 README 的模型名和可翻译英文，完成文档修改、渲染验证、残留扫描与差异审计。

## 当前决策

- 使用调用级 `model` 配置项；未提供时默认 `GPT-5.6 Pro`，保持向后兼容。
- `GPT-5.6 Thinking` 使用 `Extra High` / `极高`，并把官方 `GPT-5.6 Sol` 名称视为同一配置语义。
- `GPT-5.6 Pro` 使用 `Pro`，并把官方 `GPT-5.6 Sol Pro` 名称视为同一配置语义。
- 删除跨模型恢复链路；显式模型不匹配、自动回退或目标档位不可用时立即终止，不发送真实任务上下文。
- （Phase 1-5 的旧决策，已被 Phase 6 覆盖）当时保留 `$gpt-pro-collab` 技能标识，以避免破坏安装与显式调用兼容。
- 用户已明确将 Skill 名称迁移为 `gpt-thinking-pro-collab`；本阶段以该最新要求为准，README 中不得继续展示旧调用名称。
- 本阶段范围限定为 `README.md`；代码块、命令、路径和标识符保持 English，面向用户的说明正文使用简体中文。
- Phase 7 只把 `genoooool/gpt-pro-collab-skill` 作为内容组织与表达方式的参考，不回退本项目的名称、仓库地址、双模型配置或 fail-fast 门禁语义。
- 优化优先解决读者决策路径：先解释价值与快速开始，再展开模型、工作流、安全和维护细节；不机械复制参考 README。
- Phase 8 只借鉴参考“使用”章节的版式层级与提示词呈现方式，不复制旧 Skill 名称、单模型假设或与当前仓库不一致的任务语义。
- 除非参考证据表明必须联动，否则本阶段文件范围限定为 `README.md` 和三份规划记录。
- Phase 9 以用户最新要求为准：README 示例文本允许并应当使用简体中文，覆盖 Phase 8 的 fenced code block English-only 展示决策。
- Skill 名称、配置键、命令、路径、URL、API、模型名和其他不可翻译标识符保持原值；面向读者的任务、验收和自然语言说明改为简体中文。
- Phase 9 开始时分支一度显示领先 `origin/main` 1 个提交；最终只读核对确认 `HEAD` 与 `origin/main` 均为 `7fa01a9`。本轮不改写历史、不提交、不推送。
- Phase 9 因用户新要求直接推翻两项 README 合同，允许最小修改 `tests/test_skill_contract.py`；不修改 `SKILL.md` 或 `agents/openai.yaml` 的运行时模型集合。

## 完成标准

- [x] 存在一个面向用户的模型配置项，并有清晰文档。
- [x] 所有目标模型调用均使用配置值，不残留影响实际行为的硬编码模型。
- [x] 配置为 GPT-5.6 Thinking 时，浏览器工作流选择 `Extra High` / `极高` 并接受 Thinking / Sol 身份。
- [x] 配置为原有受支持模型或不提供配置时，既有 Pro 行为保持可用。
- [x] 自动化测试明确覆盖配置解析、模型映射、失败路径和元数据。
- [x] 官方 Skill 校验、合同测试、Python lint/format 和差异检查通过；没有意外生成物。
- [x] README 中的 Skill 标题、安装名称、调用示例和说明统一为 `gpt-thinking-pro-collab`。
- [x] README 的用户用法说明已中文化，且代码块内容保持 English。
- [x] README 差异、旧名称残留、英文说明残留和 Markdown 基础格式验证通过。
- [x] 已读取参考仓库当前 README，并形成可追踪的差异与取舍。
- [x] 本地 README 的结构、快速开始、配置说明、使用示例和边界说明经过整体优化。
- [x] 新名称、当前仓库地址、双模型语义和中文说明没有回退。
- [x] README 合同测试、旧名称残留、围栏语言、链接与差异检查通过。
- [x] 已读取参考仓库当前“使用”章节和用户截图，并形成明确的格式差异结论。
- [x] 本地 `README.md` 的“使用”章节已按参考格式调整，且保留 `gpt-thinking-pro-collab`、`model`、`mode` 与双模型语义。
- [x] Markdown 差异检查、定向文档合同和最终工作区审计通过。
- [x] 已逐张读取本轮截图，并形成模型与中文化的逐项清单。
- [x] “使用”区域所有显式 `model` 示例均为 `GPT-5.6 Pro`，README 其他模型说明符合用户指定的 Pro / Sol Pro 口径。
- [x] README 中除必要标识符外不存在可翻译的英文用户说明。
- [x] 最终 Markdown 渲染、残留扫描、差异检查和工作区审计完成。

## 错误记录

| 错误 | 尝试 | 处理 |
|---|---|---|
| 搜索表达式中的反引号被 shell 当作命令替换，输出两条 `command not found` | 1 | 未造成文件修改；后续搜索使用单引号或多个 `-e` 固定模式 |
| 官方 `quick_validate.py` 缺少运行时依赖，报 `ModuleNotFoundError: No module named 'yaml'` | 1 | 使用 `uv run --no-project --with pyyaml` 创建临时依赖环境后校验通过 |
| Ruff 检查报告 import block 和两处格式不符合规范 | 3 | 表达式与顺序已修正后仍有一行多余空白；第三次定位后使用 Ruff `--fix` 删除该空行，随后 lint 与 format 检查均通过 |
| `check-complete.sh` 无法识别表格形式的阶段，输出 `0/0 phases complete` | 1 | 按脚本要求改为可识别的阶段标题与完成状态字段后重跑 |
| 合同测试的 frontmatter 用例仍断言旧名称 `gpt-pro-collab`，与未修改的 `SKILL.md` 当前名称不一致 | 2 | Phase 6 与 Phase 7 均确认为 README 之外的既有测试契约过期；不扩大文件范围，README 相关用例和代码块语言用例均通过 |
| 新名称对应的 skills.sh 技能页是软 `404`，Snyk 深链返回 HTTP `404` | 1 | 确认当前 GitHub 仓库为私有且尚未重新收录；移除失效 badge、旧审计等级和深链，仅保留“收录后可查看”的条件式未来地址 |
| 首次追加 Phase 8 的多文件补丁因 `findings.md` 锚点与实际文件末尾不一致而整体校验失败 | 1 | 未产生任何文件修改；改为先读取文件尾部，再按稳定标题和 EOF 分文件追加 |
| 完整合同测试仍断言 `SKILL.md` 包含旧名称 `gpt-pro-collab`，9 项中 1 项失败 | 3 | README 两项定向合同均通过；该失败在任务前已存在且不涉及本轮限定的 README 范围，保留为仓库既有问题 |
| 首次完成 Phase 8 的多文件补丁因 `progress.md` 段落顺序与假定锚点不一致而整体失败 | 1 | 未产生任何文件修改；读取实际文件尾部后，分别匹配“当前阶段”和末尾证据列表 |
| 新增 README 合同测试用子串切分“## 使用”，误命中“### 使用 Skills 命令行工具” | 1 | README 内容无缺失；新增按完整二级标题行提取章节的辅助函数，避免同名前缀标题干扰 |
