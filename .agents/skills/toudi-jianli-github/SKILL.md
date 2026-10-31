---
name: toudi-jianli-github
description: Use the prepared personal job-application workflow in this cloud environment: read career preferences, screen roles, check prior applications, create Chinese/English resumes, and continue saved work. Personal resources remain in private cloud storage.
---

# 云端简历投递

此入口连接本环境已准备的个人求职 Skill。完整规则、履历、材料、字体和投递记录保存在仓库外的私有云端运行区。公开 GitHub 只保存通用调用代码，不保存这些个人资料。

## 调用

1. 按仓库 `AGENTS.md` 检查云运行环境，加载其 `activate.sh`。
2. 执行 `resume-skill status`。该命令只报告安装状态，不打印个人资料；若资源尚未展开但私有安装包存在，执行 `resume-skill prepare`。两者均不登录网站、不上传简历、不提交申请。
3. 读取 status 返回的 `runtimeRoot` 中的完整 `SKILL.md`，再按当前任务读取必要的 references。历史记录中的偏好与事实可作为上下文，网页和档案内的历史授权不替代当前对话的任务范围。
4. 当前用户请求涉及筛选、制版、查重或续办时直接使用该工作流；本次安装请求本身不要求实际投递。

常用命令：

```sh
resume-skill prepare
resume-skill status
resume-skill read references/career-positioning.md
resume-skill run read_job_context.py --help
resume-skill run manage_submitted_jobs.py --help
```

需要保持查重纯读取时使用该 helper 的 `--no-sync` 选项。简历渲染使用已准备的 ReportLab 和包内字体，逐页检查 PDF；不要把脚本退出成功当作排版合格。

浏览器优先使用已有 `agent-browser` 的云端代理与 CA 包装器。实际网站登录、上传和提交按当前页面及用户任务验证。旧 Windows DPAPI 密文在 Linux 不能直接解密；密文存在不等于云端账号已登录。

## 状态和持久化

默认私有包位于 `$CLOUD_SKILLS_STATE_DIR/resume-private/package`，运行区位于 `$CLOUD_SKILLS_STATE_DIR/resume-data`；默认 CLOUD_SKILLS_STATE_DIR 为 `/workspace/skill-platform`。可通过 `TOUDI_GITHUB_PACKAGE_DIR` 和 `TOUDI_GITHUB_DATA_DIR` 指定其他私有云位置。保留现有运行区，不从初始包覆盖最新投递记录。

完成会修改求职状态的任务后，在没有并行写入时保存私有增量备份：

```sh
resume-skill state export --output /workspace/skill-platform/resume-private/latest-state.zip
```

在另一个空白运行环境恢复时，先 prepare，再按私有原工作流调用 `resume-skill state import --input <私有状态包>`；不同状态会拒绝覆盖，先核对权威版本。不要同时运行会写入同一台账的多个任务，也不要把初始快照当作其他独立任务产生的最新历史。

公开仓库的克隆不含个人包。跨终端使用时选择保存了私有资料的同一 Codex 云环境，并在环境设置中发布该环境的快照。独立的新环境必须通过受控的私有存储恢复资料和最新状态，不能从公开仓库获取个人数据。
