# 上下文、基线与归档

目标模型不能直接访问本地仓库、终端、内部服务或未提供的文件。提供背景、目标、范围、不可破坏边界、已尝试方案、证据、交付格式和验收标准；区分事实、推断和建议，不要求它声称执行本地测试。

## 选择内容

- consult 优先使用必要片段、接口与错误日志；不为了流程创建 ZIP。
- delegate 按架构、行为、兼容性和测试依赖选文件。相关的完整设计、决策、交接、源码和测试可以全部提供；不设目标模型上下文的固定文件数量或体积上限。
- 文件白名单必须由 Codex 根据任务确定；不把 `.git`、依赖、构建输出、缓存、数据库、浏览器 / 运行状态、`.env`、证书或凭据发出。先遵守项目的数据外发政策；无法授权提供的资料不能靠扫描结果放行。
- 脚本只输出清单、大小、哈希和扫描摘要，不逐文件回传正文或完整日志。可用的专用密钥扫描器仍应执行；内置正则只能发现部分已知形式，不证明内容绝对安全。疑似秘密会停止生成，需缩小白名单或准备经核实的脱敏副本，不增加绕过扫描开关。

## 确定性归档

运行环境：Python 3.10+、Git，无第三方 Python 依赖。把下列 `$SKILL_DIR` 替换为本次实际加载 Skill 的目录；不要假定用户使用默认安装位置。路径清单每行一个相对仓库根目录的文件，支持路径中的空格，不展开通配符、不接受目录或符号链接。

```bash
python3 "$SKILL_DIR/scripts/context_bundle.py" \
  --root /path/to/project \
  --paths-file /tmp/context-paths.txt \
  --output /tmp/context.zip
```

产物为 `context.zip` 和 `context.zip.manifest.json`。manifest 保存 `baseCommit`、`dirty`、整个 ZIP 的 `archiveSha256`、文件清单及各文件 SHA-256。归档时间与文件权限固定，同一内容生成相同字节；同一路径已有相同产物时不重复写入，不同内容则拒绝覆盖。生成后核对文件清单和扫描摘要，原始基线 manifest 留在本地作为可信记录。

仅发送文本但预计接收补丁时，先保存同样的文件基线，不创建 ZIP：

```bash
python3 "$SKILL_DIR/scripts/context_bundle.py" \
  --root /path/to/project \
  --paths-file /tmp/context-paths.txt \
  --manifest-only --output /tmp/baseline.json
```

此时 `archiveSha256` / `archiveBytes` 为 `null`。预计新增文件不用加入不存在的路径；返回交付会检查新增目标仍不存在。仓库未使用 Git 时 `baseCommit` / `dirty` 为 `null`；Git 仓库尚无提交时 `baseCommit` 为 `null`，仍记录脏状态。已有文件通过各自哈希保护，工具不代替用户创建提交。

空项目可以用空路径清单配合 `--manifest-only` 保存基线，供后续新增文件验收；不生成无意义的空 ZIP。

## 上传与文本降级

先通过当前 UI 模型门禁，再发送已经核查的内容。只有页面确认附件就绪才算上传成功；自动上传不可用时按 [分批流程](browser-workflow.md#分批文本与上传) 发送必要文本。资料全部发送并确认前，不把提前生成的建议当成基于完整上下文的交付。

不读取浏览器 Cookie、本地存储、会话文件或凭据来解决上传问题。不因省略归档而省略对片段和日志中的秘密检查。
