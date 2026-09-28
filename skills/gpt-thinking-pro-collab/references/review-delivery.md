# 审查责任与交付协议

## 按任务收取交付

- consultation：收取回答、证据、假设和未解决问题，不要求 ZIP 或 manifest。
- audit：收取发现、影响、位置、优先级和验证限制；只读请求不落地候选补丁。
- implementation：优先统一 diff 或仅包含变更文件的 ZIP，另附 manifest；不同时重复粘贴所有完整文件。回复必须完整并与当前 turnId 对应，不能把阶段性代码当最终交付。

要求目标模型只声称它真实完成的工作；本地测试由 Codex 运行并单独报告。

## 审查责任

| 检查 | 责任与复用边界 |
| --- | --- |
| 任务范围、权限、用户已有改动 | Codex 根据当前请求和工作区检查，不能由模型授权 |
| 文件 / 归档哈希、源码基线、清单 | 本地机械核对；只能证明文件身份和基线一致 |
| 目标模型对自己代码的自查 | 作为作者说明和候选证据，不计作独立审核 |
| 真实独立审核 | 有审核者、版本、范围与结论证据时可复用未变化范围；只有 manifest 中的自称不够 |
| 接入语义与正确性 | Codex 聚焦实际变更，检查接口兼容、错误路径和验收目标；涉及权限、删除、迁移、执行或交易时扩大相关审查 |
| 运行测试 / 构建 | Codex 执行受影响验证与仓库必跑门禁；通过不替代未覆盖的重要检查 |

不要求重复通读整个项目。源码基线漂移、交付不完整、用户改动重叠、缺关键资料或测试失败时，扩大到受影响范围；本地适配后复查增量并重新验证。复用审核不能跳过上述接入责任，也不能扩大权限。

## Detached manifest

[示例](../assets/delivery-manifest.example.json) 中的零哈希只是结构示例，必须替换成实际值。manifest 放在交付 ZIP / diff 外部；`artifactSha256` 是交付物原始字节的 SHA-256，不包含 manifest 自身，避免自引用。

| 字段 | 含义 |
| --- | --- |
| schemaVersion | 当前为整数 `1` |
| format | `text`、`diff`、`zip` |
| baseCommit | 输入资料对应的 Git HEAD；非 Git 项目为 `null` |
| contextSha256 | 实际发送 ZIP 的哈希；只发送文本时为 `null` |
| artifactSha256 | 本次返回文件的 SHA-256；不能猜测 |
| changes | 相对路径、`add/modify/delete` 和 `baseSha256`；新增文件为 `null`，修改 / 删除取自原始本地基线 |
| review | `none/author/independent`、审核范围、说明；审核身份还需实际证据 |
| assumptions / validationCommands / risks | 必要假设、建议本地运行的命令、剩余风险；命令也是候选输入，不自动执行 |

目标模型无法实际计算哈希时，允许它将未知哈希标为 `null` 并说明原因；Codex 收取原始文件后本地计算，记录“本地补全、未经目标模型核算”，再形成可验收 manifest。源码基线和原始文件哈希只能从先前保留的可信记录补全，不能用当前工作树重新冒充旧基线。缺失证据不能虚构。

纯文本咨询不需要本工具；需要保存文本交付身份时，可用 `format: text`、空 `changes` 和实际文件哈希。

## 只读机械检查

```bash
python3 "$SKILL_DIR/scripts/verify_delivery.py" \
  --root /path/to/project \
  --artifact /tmp/delivery.diff \
  --manifest /tmp/delivery-manifest.json \
  --baseline /tmp/context.zip.manifest.json
```

所有代码交付需要发送前的本地基线，文本传递使用 `baseline.json`。工具核对完整交付物哈希、context 身份、Git HEAD、受影响文件的当前哈希、新增文件冲突和路径安全；无关的脏文件不阻止接入，重叠变更会被拒绝。

- ZIP 只包含声明的新增 / 修改文件；删除仅在清单中声明。拒绝越界路径、重复 / 大小写冲突、符号链接和特殊文件。默认最大展开体积 128 MiB，可按明确交付规模调整 `--max-expanded-bytes`；这是不可信交付物的资源保护，不是目标模型上下文上限。
- diff 在临时目录复制受影响文件后运行 Git 适用性检查和试应用，核对真实影响范围；不修改用户工作树或索引。重命名 / 复制使用明确的增删文件，二进制修改使用 ZIP。
- 成功输出仍包含 `requiresCodexReview: true`、`appliedToWorkspace: false`。机械检查不证明代码正确、不授权执行交付物、不应用到仓库。

完成聚焦审查和必要的执行权限核对后，Codex 才在已授权实现任务中应用必要改动，保留用户其他修改。最后运行真实测试，保留失败证据并循环修正。只读任务始终交付报告。
