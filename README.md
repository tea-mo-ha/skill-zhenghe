# skill-整合 (Skill Zhenghe)

> A local-first AI skill orchestration system for Antigravity and Codex.

面向 Antigravity 与 Codex 的本地优先 AI Skill 编排系统。

---

## 这是什么

一个 **Skill 编排仓库**，统一入口是 [`skill-suite-orchestrator`](skill-suite-orchestrator/SKILL.md)。

它不是把所有 skill 拼成一个大提示词，而是一个 **认知调度层**：

- 只从真实存在的子 skill 目录中选取最小必要集
- 先输出 `chosen_subskills`，再进入 `plan → execution → validation`
- 默认坚持 **最小必要集**，避免全量激活
- 不允许虚构 skill、不允许把子 skill 原文拼接成单一 prompt

## 支持什么场景

| 场景 | 入口 Skill | 描述 |
|------|-----------|------|
| 🔍 **项目审核** | `code-review-and-quality` | 多维度代码审查 |
| 🏗 **架构分析** | `spec-driven-development` → `api-and-interface-design` | 规格驱动的架构评估 |
| 🎨 **页面生成** | `frontend-design` / `frontend-ui-engineering` | 从设计到生产级 UI |
| 🐞 **调试修复** | `systematic-debugging` / `debugging-and-error-recovery` | 根因定位与修复 |
| 🌐 **浏览器验证** | `webapp-testing` / `agent-browser` | 本地 Web 应用自动化测试 |
| 🚀 **交付上线** | `shipping-and-launch` | 发布前检查清单与部署 |
| 📋 **文件规划** | `planning-with-files-zh` | 基于文件的中文任务规划 |

## 怎么接入

### Antigravity（反重力）

将本仓库内的 skill 目录符号链接至 Antigravity 运行时路径：

```bash
# 示例：链接 addy-skills 下的子 skill
ln -s /path/to/skill-zhenghe/addy-skills/* ~/.gemini/antigravity/skills/

# 示例：链接 extra-skills
ln -s /path/to/skill-zhenghe/extra-skills/* ~/.gemini/antigravity/skills/

# 示例：链接 orchestrator 本身（唯一总控入口）
ln -s /path/to/skill-zhenghe/skill-suite-orchestrator ~/.gemini/antigravity/skills/
```

> **架构提示**：此处采用全展平（flatten）挂载机制。`skill-suite-orchestrator` 完全基于注入的上下文和技能名称进行解耦调度，不再依赖相对目录结构，以此实现对 Antigravity 等环境的天然兼容，并支持严格拦截原生平台技能。

Antigravity 会自动从 `~/.gemini/antigravity/skills/` 发现并加载 skill。

### Codex

Codex 通过 `.codex/AGENTS.md` 仓库级策略文件来读取配置。该文件已包含在本仓库中。

## 怎么使用

只需自然语言，orchestrator 自动路由到最小必要 skill 集：

```
"审核这个项目"
"分析这个架构"
"帮我生成一个产品落地页"
"调试这个报错"
"帮我做一次浏览器回归验证"
"准备上线，跑一遍检查清单"
```

**输出契约：**

```md
chosen_subskills
- skill-name: 选择理由

plan
- ...

execution
- ...

validation
- ...
```

## 目录说明

```
skill-zhenghe/
├── skill-suite-orchestrator/   # 统一入口 — 认知调度层
│   ├── SKILL.md                # 总控协议 + 审计跟踪契约
│   ├── references/             # 路由矩阵 & 技能清单
│   └── agents/                 # 代理配置
├── addy-skills/                # 工程流程类基础 skill（20 个，managed）
├── extra-skills/               # 页面设计、浏览器自动化等补充 skill（3 个，managed）
├── plugins/                    # 不纳入默认路由的插件 & deprecated skills
├── CHANGELOG.md                # 版本变更记录
└── .codex/AGENTS.md            # Codex 仓库级策略
```

> **Provenance 说明**：`addy-skills/` 和 `extra-skills/` 下的 skill 是 **managed**（SKILL.md 由本仓库版本控制）。`brainstorming`、`systematic-debugging` 等 7 个 skill 是 **platform-native**（由宿主平台提供），仅在 `skill-inventory.md` 中记录路由描述，不在本仓库中存放副本，以避免版本漂移。

## 路由维护

- **技能清单** → [`skill-suite-orchestrator/references/skill-inventory.md`](skill-suite-orchestrator/references/skill-inventory.md)
- **场景路由** → [`skill-suite-orchestrator/references/routing-matrix.md`](skill-suite-orchestrator/references/routing-matrix.md)
- **总控协议** → [`skill-suite-orchestrator/SKILL.md`](skill-suite-orchestrator/SKILL.md)
- **版本变更** → [`CHANGELOG.md`](CHANGELOG.md)

## 默认边界

- `plugins/` 下的内容不纳入默认总控路由
- Deprecated skills（如 `using-agent-skills`）不参与任何路由
- 不允许虚构 skill
- 不允许把全部 skill 一次性启用
- 不允许把子 skill 原文直接拼接成单一大 prompt
- 不允许将 platform-native skill 的 SKILL.md 复制到本仓库

## License

MIT

