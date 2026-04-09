# skill-整合

这个工程现在对外只保留一个统一入口：

- `skill-suite-orchestrator`

它不是把所有 skill 拼成一个大提示词，而是一个认知调度层：

- 只从真实存在的 `addy-skills`、`extra-skills`、`copied-existing-skills` 中选子 skill
- 先输出 `chosen_subskills`
- 再进入 `plan`、`execution`、`validation`
- 默认坚持“最小必要集”，避免全量激活

## 目录说明

- `addy-skills/`: 工程流程类基础 skill
- `extra-skills/`: 页面设计、浏览器自动化、本地 Web 验证等补充 skill
- `copied-existing-skills/`: 复制引入的通用 skill
- `skill-suite-orchestrator/`: 新的统一入口 skill

## 如何使用

在 Codex 或反重力里，只暴露并调用：

- `skill-suite-orchestrator`

不要直接把全部子 skill 一起挂到同一个任务里。总控 skill 会根据用户意图自动挑选最小必要集。

推荐的输出契约：

```md
chosen_subskills
- ...

plan
- ...

execution
- ...

validation
- ...
```

## 路由维护

- 技能清单维护在 `skill-suite-orchestrator/references/skill-inventory.md`
- 场景路由维护在 `skill-suite-orchestrator/references/routing-matrix.md`
- 总控协议维护在 `skill-suite-orchestrator/SKILL.md`

## 默认边界

- `plugins/` 下的内容不纳入默认总控路由
- 不允许虚构 skill
- 不允许把全部 skill 一次性启用
- 不允许把子 skill 原文直接拼接成单一大 prompt
