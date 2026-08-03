# 调研发现

## 当前状态

- 工作目录：`/Users/zhangjinhui/Desktop/gpt-thinking-collab-skill`
- Git 分支：`main`，初始状态与 `origin/main` 一致且无工作区修改。
- 项目根目录初始不存在 `task_plan.md`、`findings.md`、`progress.md`。
- 本地记忆索引中未找到该仓库或 GPT-5.6 Thinking 改造的既有记录，因此后续结论以当前源码为准。
- 仓库仅包含 `README.md`、`SKILL.md` 和 `agents/openai.yaml`，没有应用代码、依赖清单或自动化测试框架。

## 当前实现证据

- `SKILL.md` 的“强制模型门禁”把目标模型固定为 `GPT-5.6 Pro`。
- 新对话的 UI 模式固定为 `Pro`；只有特殊恢复链路才临时切换到 `极高`。
- 回复验收只接受 `GPT-5.6 Pro` 或 `5.6 Pro`，并明确拒绝 `5.6 Thinking`。
- README 的流程图、前置条件、使用说明、失败文案和最终报告同样围绕 Pro 写死。
- `agents/openai.yaml` 的显示文案和默认提示要求先通过 GPT-5.6 Pro 门禁。
- 因为项目本质是声明式 Skill，模型“调用链”是浏览器操作指令，不涉及 OpenAI SDK 或 API 请求字段。
- Git 历史只有一个初始化提交，没有更早设计讨论或迁移约束可供复用。
- `.gitignore` 只覆盖编辑器、临时文件和常见秘密文件；没有测试或生成物约定。
- README FAQ 明确把“最终不是 GPT-5.6 Pro 就失败”定义为现有硬性条件，因此本次改造需要有意识地把该条件替换为“必须匹配配置模型”，而不是简单追加 Thinking 别名。
- `GPT Pro` 还被用作外部角色名称、`delegate` 模式标题、上下文提供方和最终报告主体；若只修改门禁，这些指令在选择 Thinking 时会产生语义冲突。

## 初步设计方向

- 引入一个面向调用方的 `model` 配置项，由 Skill 在解析调用时读取。
- 模型配置必须同时决定 UI 推理模式与自报回复的精确验收集合，避免“界面选了 A、实际却接受 B”。
- 至少应原生支持：
  - `GPT-5.6 Pro` 对应 `Pro` 模式；
  - `GPT-5.6 Thinking` 对应 `极高` 模式。
- 未指定配置时需要稳定的默认模型，以保持现有调用兼容；默认值应根据仓库现有语义优先保留为 `GPT-5.6 Pro`，除非后续证据要求改变。
- 配置了某个模型后不得自动降级或切换到另一模型；门禁失败应报告期望值与实际识别值。

## Skill 规范

- `SKILL.md` frontmatter 只能包含 `name` 和 `description`；模型配置不能新增为任意 frontmatter 字段。
- `agents/openai.yaml` 是 UI 元数据，不是适合承载每次调用模型选择的运行配置。
- `interface.default_prompt` 必须显式包含 `$gpt-pro-collab`，并应与更新后的配置语法一致。
- 对现有 Skill 的改造应保持 `SKILL.md` 指令使用祈使语气，并在完成后运行 `quick_validate.py`。
- 当前 `SKILL.md` 为 167 行，远低于 500 行建议上限；两种模型映射无需额外拆分 reference 文件。
- Skill 修改后需要核对 `agents/openai.yaml` 与 `SKILL.md` 一致，并适合用现实调用样例做前向验证。

## 当前官方产品事实

- OpenAI 帮助中心当前把标准 ChatGPT 中的模型与推理档位表述为：
  - `Medium`、`High`、`Extra High` 使用 `GPT-5.6 Sol`；
  - `Pro` 使用 `GPT-5.6 Sol Pro`。
- 2026-06-10 的模型选择器更新把旧 `Thinking Heavy` 重命名为 `Extra High`；因此项目中的 `GPT-5.6 Thinking` 应作为兼容配置别名映射到 `Extra High` / 本地化的 `极高`，并接受 `GPT-5.6 Sol` 作为官方自报名。
- OpenAI 说明推理额度耗尽后可能回退到 `GPT-5.4 Thinking mini`。这与“配置哪个模型就用哪个模型”冲突，因此工作流必须在 UI 显示回退、限额或模型变更时停止，不能静默继续。
- 官方来源：
  - <https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt>
  - <https://help.openai.com/es-419/articles/6825453-chatgpt-release-notes>

## 配置契约结论

- 采用调用级单一配置项 `model`，而不是新增 Skill frontmatter、自定义 `agents/openai.yaml` 字段或持久化配置文件。
- 未配置 `model` 时默认 `GPT-5.6 Pro`，保持现有调用兼容。
- 支持两个语义配置：
  - `GPT-5.6 Pro`，兼容官方名称 `GPT-5.6 Sol Pro`；
  - `GPT-5.6 Thinking`，兼容官方名称 `GPT-5.6 Sol`，固定使用 `Extra High` / `极高` 推理档位。
- 显式配置后不得通过现有 `Pro → 极高 → Pro` 链路切换目标，也不得接受另一个模型配置；不匹配立即终止。
- 未知值、冲突值或目标档位不可用时在发送任何任务上下文前失败，并报告配置值与支持值。

## 前向验证结果

- 独立只读实例在未提供 `model` 时解析为：
  - `targetModel = GPT-5.6 Pro`
  - `reasoningMode = Pro`
  - 四个 Pro / Sol Pro 身份别名
  - `consult` 模式下先本地工作，不会无条件打开浏览器
- 独立只读实例在 `model: GPT-5.6 Thinking` 时解析为 `Extra High` / `极高` 和 Thinking / Sol 身份集合。
- 独立只读实例在 `model: GPT-5.6 Sol` 时正确归一化到 Thinking 配置语义。
- 独立只读实例在 `model: GPT-5.5 Instant` 时拒绝进入浏览器门禁，且没有回退到默认 Pro。
- 四条结果都来自只读取最终 `SKILL.md` 的隔离任务，没有读取规划文件或预期答案。

## 完成审计

| 要求 | 权威证据 | 结论 |
|---|---|---|
| 单一模型配置项 | `SKILL.md` 定义调用级 `model`；README 提供配置表和实例 | 已满足 |
| GPT-5.6 Thinking 兼容 | Thinking / Sol 映射到 `Extra High` / `极高`，身份集合覆盖兼容名和官方名 | 已满足 |
| 配置哪个模型就使用哪个模型 | 门禁使用解析后的 `reasoningMode` 与 `acceptedIdentities`；不匹配、未知值、限额回退均终止 | 已满足 |
| 既有 Pro 兼容 | 缺省值和 UI 默认提示均为 `GPT-5.6 Pro`；兼容 `GPT-5.6 Sol Pro` 自报名 | 已满足 |
| 文档与元数据同步 | README、流程图、FAQ、`agents/openai.yaml` 均展示可配置模型语义 | 已满足 |
| 自动化覆盖 | 9 项合同测试覆盖默认值、两套映射、fail-fast、回退、元数据和语言规范 | 已满足 |
| 独立行为验证 | 四个隔离只读实例正确解析默认 Pro、Thinking、Sol 别名和未知值 | 已满足 |
| 项目质量门禁 | 官方校验、Ruff、空白、模板残留和 Git 差异检查通过 | 已满足 |

## 审计中修正的问题

- UI 默认提示最初预填 Thinking，会改变既有默认行为；现已改回显式 Pro。
- Python 合同测试最初直接包含中文字符串常量；现已改为 ASCII-only Unicode escape 或 English 结构匹配，并增加源码 ASCII-only 测试。
- Python 测试首次生成 `__pycache__`；已删除并精确更新 `.gitignore`。

## 剩余风险

- 模型身份仍来自自然语言自报，不是平台侧加密证明；README 已明确该限制。
- ChatGPT UI 档位名称可能继续变化；README 链接官方说明，Skill 在目标档位不存在时会安全失败。
- 未执行真实 ChatGPT 对话，因为本次目标是改造和验证 Skill，本地前向验证在浏览器动作前停止，未使用用户账号或额度。
