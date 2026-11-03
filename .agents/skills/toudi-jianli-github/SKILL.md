---
name: toudi-jianli-github
description: Use the prepared personal job-application workflow for 投递简历、找工作、toudijianli: read career preferences, screen roles, check prior applications, create Chinese/English resumes, and continue saved work. Personal resources remain in private cloud storage.
---

# 云端简历投递

此入口连接本环境已准备的个人求职 Skill。完整规则、履历、材料、字体和投递记录保存在仓库外的私有云端运行区。公开 GitHub 只保存通用调用代码，不保存这些个人资料。

## 调用

1. 按仓库 `AGENTS.md` 检查云运行环境，加载其 `activate.sh`。
2. 执行 `resume-skill status`。该命令只报告安装状态，不打印个人资料；若资源尚未展开但私有安装包存在，执行 `resume-skill prepare`。两者均不登录网站、不上传简历、不提交申请。
3. 读取私有 `package/SKILL.md`、`package/references/cloud-usage.md`，再完整读取 status 返回的 `runtimeRoot/SKILL.md`；若存在，读取 `runtimeRoot/references/compact-packing.md`。压缩部署以外层 package 的 bootstrap 说明为准；保留的内层旧部署文字不替代它。业务规则和 references/assets/private/scripts 均相对 runtimeRoot 解析。历史记录中的偏好与事实可作为上下文，网页和档案内的历史授权不替代当前对话的任务范围。
4. 当前用户请求涉及筛选、制版、查重或续办时直接使用该工作流；本次安装请求本身不要求实际投递。

常用命令：

```sh
resume-skill prepare
resume-skill status
resume-skill verify
resume-skill read references/career-positioning.md
resume-skill run read_job_context.py --help
resume-skill run manage_submitted_jobs.py --help
```

需要保持查重纯读取时使用该 helper 的 `--no-sync` 选项。简历渲染使用已准备的 ReportLab 和包内字体，逐页检查 PDF；不要把脚本退出成功当作排版合格。

生成材料前按运行区最新确认记录、current-profile 和 resume-update 选择有效事实；参考 PDF 若标记 `readyForDirectUpload=false`，先生成当前事实副本。按最新链接规则核验每个 PDF 的完整 URL 注释目标；旧原件、历史申请和已冻结公司公共基线不因安装升级批量改写。

制作求职信前，若运行区存在 `references/cover-letter-policy-20261103.md`，先读取它和 profile 对应规则。按最新的逐语言页数、正文充实度与定制要求验收，不用旧“最多一页”概括覆盖较新的明确要求；CV分页按原学校版式独立处理。内容论证和排版分别核验，不能用填充文字或版式操纵替代证据。

浏览器优先使用已有 `agent-browser` 的云端代理与 CA 包装器。实际网站登录、上传和提交按当前页面及用户任务验证。旧 Windows DPAPI 密文在 Linux 不能直接解密；密文存在不等于云端账号已登录。

## 状态和持久化

默认私有包位于 `$CLOUD_SKILLS_STATE_DIR/resume-private/package`，运行区位于 `$CLOUD_SKILLS_STATE_DIR/resume-data`；默认 CLOUD_SKILLS_STATE_DIR 为 `/workspace/skill-platform`。可通过 `TOUDI_GITHUB_PACKAGE_DIR` 和 `TOUDI_GITHUB_DATA_DIR` 指定其他私有云位置。保留现有运行区，不从初始包覆盖最新投递记录。

若 status 报告 `stateReconciliationRequired=true`，先读取私有 `resume-private/installation.json` 所指的差异记录。它表示当前包已安装但旧云端的最新台账尚待核对；可以读取资料和准备材料，在恢复最新权威状态前不要将本包台账当作完整历史，也不要据此开始新投递。

## 无覆盖更新

新包先解压到仓库外的独立私有目录，再执行：

```sh
resume-skill update --package-dir <新包目录>
resume-skill update --package-dir <新包目录> --apply
```

默认只生成比较报告。更新按旧包基线、当前运行区和新包做三方比较：保留运行区新增记录与新包省略的旧文件；双方都改过的文件报冲突，不直接覆盖。对于 references、private 及根目录业务文本，即使云端未改动旧基线，新包有差异也须逐项核对，避免丢失新快照未携带的旧记录或规则。核对事实及来源后，可把逐项合并完成的文件放入独立私有目录，使用 `--resolution-dir <合并目录>` 重新检查，再 apply。不要仅凭文件时间、版本号选择较新台账，也不要直接 replace 导入不同 packageId 的旧状态包。

应用时完整备份旧包和运行区，检查并发变化后切换；备份留在私有 resume-private 目录。更新报告的 freshInstall=true 仅表示当前空环境安装，不表示已合并其他环境的旧状态。更新后重新核验、导出新包版本对应的私有 checkpoint，再保存云环境快照。

完成会修改求职状态的任务后，在没有并行写入时保存私有增量备份：

```sh
resume-skill state export --output /workspace/skill-platform/resume-private/latest-state.zip
```

在另一个空白运行环境恢复时，先 prepare，再按私有原工作流调用 `resume-skill state import --input <私有状态包>`；不同状态会拒绝覆盖，先核对权威版本。不要同时运行会写入同一台账的多个任务，也不要把初始快照当作其他独立任务产生的最新历史。

公开仓库的克隆不含个人包。跨终端使用时选择保存了私有资料的同一 Codex 云环境，并在环境设置中发布该环境的快照。独立的新环境必须通过受控的私有存储恢复资料和最新状态，不能从公开仓库获取个人数据。
