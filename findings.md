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

## README 名称迁移与中文化任务

- 用户明确指定新的 Skill 名称为 `gpt-thinking-pro-collab`。
- 用户明确要求修改范围为 `README.md`，重点修正仍为英文的用法说明。
- 当前工作区在任务开始时无未提交修改；已有三份规划文件来自上一项已完成任务。
- 本次审校将区分用户可见说明与字面语法：说明正文翻译为简体中文，命令、代码块、路径、配置键和其他标识符保持 English。
- `SKILL.md` frontmatter 已声明 `name: gpt-thinking-pro-collab`，可作为 README 的 Skill 名称依据。
- Git `origin` 已指向 `https://github.com/jay6697117/gpt-thinking-pro-collab-skill.git`，README 中原有的 `genoooool/gpt-pro-collab-skill` 已不是当前仓库地址。
- README 的旧名称覆盖 badge、显式触发、Skills CLI、skills.sh 页面、GitHub 克隆目录、手动目录结构、四组使用示例、更新命令和安全审计链接，必须作为一组原子迁移。
- README 主体说明已大部分中文化；明显的英文用户用法集中在四组示例的任务与验收文本。为同时保持代码块 English，将把中文任务描述移到代码块外，代码块仅保留 Skill 调用与配置语法。
- `SKILL.md` 描述、`agents/openai.yaml` 和现有合同测试仍引用旧触发名，但它们不属于用户本轮明确要求修改的 `README.md` 范围；本轮只记录该事实，不扩大修改范围。
- 修改后 README 已无 `gpt-pro-collab` 或 `genoooool` 残留；标题、链接、命令、目录和用法位置已统一使用新名称。
- README fenced code block 的 English-only 合同测试通过；围栏外纯英文说明扫描无结果，四组用户任务与验收示例均已改为简体中文。
- 完整合同测试共 9 项，8 项通过；唯一失败是未修改的 `tests/test_skill_contract.py` 仍要求 `SKILL.md` 包含旧名称，而 `SKILL.md` 当前已是新名称。README 文档合同与 Markdown 语言合同均通过。
- GitHub CLI 确认 `jay6697117/gpt-thinking-pro-collab-skill` 真实存在且当前为私有仓库，解释了匿名 GitHub 页面返回 `404` 的原因。
- 新名称对应的 skills.sh 技能页尚未收录：HTTP 表面返回 `200`，但页面正文明确显示 `404`；Snyk 深链直接返回 HTTP `404`。
- README 不应把旧名称下的 Snyk 审计等级自动继承给新名称。顶部 badge、具体等级和失效深链已移除；安装章节保留了明确带“收录后”前提的未来技能页地址。

## README 参考仓库优化任务

- 用户指定参考仓库：`https://github.com/genoooool/gpt-pro-collab-skill`。
- 当前本地仓库为 `/Users/zhangjinhui/Desktop/gpt-thinking-pro-collab-skill`；本轮开始时 Git 工作区干净，上一轮 README 与规划记录已成为当前基线。
- 本轮修改范围仍限定为 `README.md`，参考仓库只用于提炼信息架构和表达，不覆盖本地源码已经确定的新名称与双模型行为。
- 已读取参考仓库当前 `main` 分支 README。参考文档的核心结构是：价值说明、角色、`consult` / `delegate`、模型门禁、前置条件、三种安装方式、使用示例、执行流程、安全、权限、最终报告、更新、验证、限制和 FAQ。
- 本地 README 已继承上述大部分章节，并额外加入双模型配置、参数化门禁、合同测试和新的安全说明；因此本轮不需要机械补章节，而应优化信息优先级和重复内容。
- 当前本地 README 的主要可用性问题：
  - 首次可执行的安装步骤位于百余行之后，新用户需要先读大量实现细节；
  - “解决什么问题”“角色分工”“协作模式”“执行流程”“最终报告”存在部分语义重复；
  - 模型配置表完整，但缺少一个把安装、触发、模式与模型选择串起来的快速路径；
  - 文档较长但没有面向不同读者的导航入口；
  - skills.sh 尚未收录新私有仓库，相关地址必须继续保持条件式说明。
- 参考仓库值得保留的设计：Codex 最终负责、目标模型只提供候选交付、两种协作模式、模型门禁、安全白名单、权限不自动扩大和本地独立验收。
- 参考仓库不可带回的内容：`gpt-pro-collab` 旧名称、`genoooool` 地址、只接受 GPT-5.6 Pro 的单模型假设，以及 `Pro → 极高 → Pro` 的跨模型恢复链路。
- 参考 README 的中文任务示例放在 fenced code block 中；本地合同要求 fenced code block 保持 English，因此继续采用中文 blockquote 与 English 标识符组合。
- `SKILL.md` 确认 README 必须准确表达的运行合同：
  - Skill 由用户显式触发，默认使用 `consult`；
  - 每次调用只允许一个 `model`，缺省为 `GPT-5.6 Pro`；
  - Pro 与 Thinking 分别映射到 `Pro` 与 `Extra High` / `极高`；
  - 未知、缺失或冲突配置在浏览器动作前失败；
  - 每个新对话都要执行模型门禁，且运行中发生模型变化或额度回退时立即停止；
  - 目标模型不能直接访问本地环境，Codex 负责上下文准备、接入、权限控制和客观验证。
- `tests/test_skill_contract.py` 对 README 的直接约束是：必须保留 `## 模型配置`、`model: GPT-5.6 Thinking`、Sol 与 Extra High 映射、禁止跨模型继续的表述，并确保全部 fenced code block 不含 Han 字符。
- `agents/openai.yaml` 与测试仍使用旧触发名，但本轮用户只要求优化 README；这项仓库级不一致继续作为外部已知问题记录，不在 README 重构中掩盖或修复。
- 确定的 README 新结构：
  1. 一句话价值与核心原则；
  2. 文档导航和可立即执行的快速开始；
  3. 适用边界、角色与模式；
  4. 模型配置与强制门禁；
  5. 完整安装、更新和使用示例；
  6. 执行流程、安全、权限与最终交付；
  7. 仓库验证、限制和 FAQ。
- 第一轮 diff 审阅确认新名称、模型映射和门禁语义均未回退；参考仓库旧名称只出现在明确标注的演进来源链接中。
- 第一轮重构新增快速开始后，原“前置条件”成为重复内容；源码安全、权限边界和浏览器提示注入防护也仍分散在三个位置。最终版将删除重复前置条件，并合并为单一“安全与权限”章节。
- README 定向合同测试 2 项全部通过：双模型文档合同与 fenced code block English-only 约束均满足。
- `git diff --check` 通过；围栏外纯英文行扫描只匹配规范 Skill 标题，没有残留英文用法说明。
- 完整合同测试仍为 9 项中 8 项通过，唯一失败与 Phase 6 相同：测试文件仍断言未修改 `SKILL.md` 中的旧名称。README 相关测试没有新增失败。
- `gpt-pro-collab` 和 `genoooool` 在 README 中只出现一次，位于“演进说明”的明确参考仓库名称与链接；不存在旧安装命令、旧触发名或旧目录残留。
- 外部链接验证结果：
  - 参考 GitHub 仓库页面返回 HTTP `200`；
  - OpenAI 两条帮助页对裸 `curl` 返回防自动化 `403`，但页面读取确认标题与正文均可访问；
  - 官方 GPT-5.6 页面确认 `Extra High` 使用 GPT-5.6 Sol、`Pro` 使用 GPT-5.6 Sol Pro，额度耗尽时可能回退到 GPT-5.4 Thinking mini，与 README 当前映射和 fail-fast 说明一致；
  - 新 skills.sh 地址仍显示未收录的软 `404`，README 已明确以“收录后”为前提，没有把它描述为当前可用页面。
- 最终 README 通过 GitHub GFM 渲染接口，导航目标、围栏结构和 Markdown 语法可正常解析。
- 最终优化保留参考文档的角色分工、安全和验收优势，同时把安装与首次调用提前，并明确呈现本项目的双模型扩展与严格 fail-fast 差异。
