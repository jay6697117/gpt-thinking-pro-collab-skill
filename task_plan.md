# 任务计划：GPT-5.6 Thinking 与可配置模型兼容

## 目标

将当前项目改造为兼容 GPT-5.6 Thinking，并提供一个明确的配置项；运行时必须使用该配置项指定的模型，而不是在业务代码中写死模型。

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

## 当前决策

- 使用调用级 `model` 配置项；未提供时默认 `GPT-5.6 Pro`，保持向后兼容。
- `GPT-5.6 Thinking` 使用 `Extra High` / `极高`，并把官方 `GPT-5.6 Sol` 名称视为同一配置语义。
- `GPT-5.6 Pro` 使用 `Pro`，并把官方 `GPT-5.6 Sol Pro` 名称视为同一配置语义。
- 删除跨模型恢复链路；显式模型不匹配、自动回退或目标档位不可用时立即终止，不发送真实任务上下文。
- （Phase 1-5 的旧决策，已被 Phase 6 覆盖）当时保留 `$gpt-pro-collab` 技能标识，以避免破坏安装与显式调用兼容。
- 用户已明确将 Skill 名称迁移为 `gpt-thinking-pro-collab`；本阶段以该最新要求为准，README 中不得继续展示旧调用名称。
- 本阶段范围限定为 `README.md`；代码块、命令、路径和标识符保持 English，面向用户的说明正文使用简体中文。

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

## 错误记录

| 错误 | 尝试 | 处理 |
|---|---|---|
| 搜索表达式中的反引号被 shell 当作命令替换，输出两条 `command not found` | 1 | 未造成文件修改；后续搜索使用单引号或多个 `-e` 固定模式 |
| 官方 `quick_validate.py` 缺少运行时依赖，报 `ModuleNotFoundError: No module named 'yaml'` | 1 | 使用 `uv run --no-project --with pyyaml` 创建临时依赖环境后校验通过 |
| Ruff 检查报告 import block 和两处格式不符合规范 | 3 | 表达式与顺序已修正后仍有一行多余空白；第三次定位后使用 Ruff `--fix` 删除该空行，随后 lint 与 format 检查均通过 |
| `check-complete.sh` 无法识别表格形式的阶段，输出 `0/0 phases complete` | 1 | 按脚本要求改为可识别的阶段标题与完成状态字段后重跑 |
| 合同测试的 frontmatter 用例仍断言旧名称 `gpt-pro-collab`，与未修改的 `SKILL.md` 当前名称不一致 | 1 | 确认为 README 之外的既有测试契约过期；本轮不扩大文件范围，README 相关用例和代码块语言用例均通过 |
| 新名称对应的 skills.sh 技能页是软 `404`，Snyk 深链返回 HTTP `404` | 1 | 确认当前 GitHub 仓库为私有且尚未重新收录；移除失效 badge、旧审计等级和深链，仅保留“收录后可查看”的条件式未来地址 |
