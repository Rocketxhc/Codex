# Codex 云端技能环境

此仓库保存 Skill 源码和可重建的云端运行配置。手机、平板或电脑均可通过 **Codex 云端任务**使用：选择 `Rocketxhc/Codex` 仓库和配套云环境，然后直接描述要做的事情。任务在云机器上运行，无需在个人设备安装这些 Skill。

`AGENTS.md` 会引导后续 agent 自动选择相关技能、检查依赖，并按需恢复运行环境。GitHub 保存可复用版本；云端任务负责执行。

| 能力 | 已安装 Skill |
| --- | --- |
| 网页访问和自动操作 | `agent-browser` |
| 云端图形桌面操作 | `computer-use-cloud` |
| Word、PDF、PPT | `document-creator`、`pdf`、`presentation-creator` |
| 图片生成和编辑工作流 | `imagegen`，使用平台内置图片工具 |
| 架构评审与配套流程 | `improve-codebase-architecture`、`codebase-design`、`grilling`、`domain-modeling` |

例如：“用云端浏览器读取这个页面”“制作一份可编辑的中文 PPT”“把这份内容生成 Word 和 PDF”。架构评审需明确调用对应 Skill。

## 云环境配置

在支持本平台运行时的云环境中，安装脚本使用：

```bash
cd /workspace/Codex
bash .cloud/bootstrap.sh --register
```

后续任务启动时读取 `AGENTS.md`，执行：

```bash
cd /workspace/Codex
bash .cloud/bootstrap.sh --check
source /workspace/skill-platform/activate.sh
```

首次缺少依赖时运行 bootstrap 安装；已准备的环境通过只读检查后直接复用。脚本使用仓库内的源码、固定 Python 版本和 npm 锁文件，不依赖旧聊天会话中的上传附件或源码压缩包。支持 `CLOUD_SKILLS_STATE_DIR` 指定独立的云端运行目录。

运行环境需要 Codex 云基础镜像提供 Python 3.12、Node 24+、Chromium、LibreOffice、Poppler 和 Xorg dummy 显示驱动等系统工具；脚本会检查这些条件。浏览器和桌面服务按任务需要启动，不需要长期保持这次会话的进程。

Skill 原文位于 `.agents/skills`。部分技能带隐藏标记，当前聊天菜单也可能不动态刷新；后续 agent 可通过 `AGENTS.md` 的明确路径直接读取调用。

## 保存范围与验证

仓库保存技能、许可证、依赖锁文件和恢复脚本。登录态、密钥、个人简历、浏览器用户资料、依赖目录和运行日志留在私有云端运行目录，不能提交到仓库。通用 Word/PPT Skill 是独立编写的开放工具流程，其余上游来源保存在对应许可证和来源文件中。

已在当前云机器验证浏览器读取/填表/点击/截图和 HTTPS、中文 Word/PDF/PPT 生成与渲染、桌面鼠标/中英文输入及重启。新框架还通过了隔离空目录与全新 Git 克隆的依赖恢复、中文 Word/PPT 导出 PDF 和浏览器填表测试。图片工作流已安装，未在安装阶段实际生成图片，也不保证指定 Image 2 模型。验证范围见 [.cloud/VALIDATION.md](.cloud/VALIDATION.md)，个人运行资料不提交仓库。

**待完成：简历投递 Skill。** 两次提供的 RAR 都超过平台单文件 32 MiB 传输限制，尚未读取、安装或测试。请提供小于限制的源码包（去掉 node_modules、虚拟环境、浏览器缓存等），或可访问的源码仓库/HTTPS 地址。安装完成后才会加入自动调用入口。

GitHub 配置提交和云环境发布是独立步骤：云配置保存后，仍需在平台环境设置中保存并发布，后续选择该环境的任务才能恢复相应快照。全新克隆也可通过上述脚本重建依赖。
