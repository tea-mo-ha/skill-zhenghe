# Skill Inventory

> Authoritative catalog for orchestrator routing. Updated: 2026-04-14.

This inventory distinguishes between **managed skills** (SKILL.md lives in this repo, version-controlled by us) and **platform-native skills** (provided by the host runtime, referenced for routing but not version-managed here).

## Version Governance

- **Managed skills** (`addy-skills/`, `extra-skills/`): Changes flow through this repository's Git history. Orchestrator routing and runtime execution are guaranteed to reference the same SKILL.md.
- **Platform-native skills**: The host platform (Antigravity / Codex) owns the SKILL.md. This inventory records only the routing description. If the platform updates a native skill's behavior, the orchestrator's routing decisions remain valid because they depend on intent classification, not on the skill's internal implementation.
- **Rule**: Do not copy platform-native SKILL.md files into this repository. Copies create hidden version drift between routing expectations and runtime execution.

---

## Managed: addy-skills

> Source: `addy-skills/` — 20 skills, fully managed.

| Skill | 用途 |
| --- | --- |
| `api-and-interface-design` | 设计 API、模块边界、类型契约和前后端接口。 |
| `browser-testing-with-devtools` | 用真实浏览器和 DevTools 检查 DOM、console、network、performance。 |
| `ci-cd-and-automation` | 配置或修改 CI/CD、质量门禁、自动化流水线。 |
| `code-review-and-quality` | 做多维代码审核，重点看正确性、可读性、架构、安全和性能。 |
| `code-simplification` | 在不改行为的前提下简化代码结构和复杂度。 |
| `context-engineering` | 在新会话、上下文混乱或输出质量下降时整理上下文与规则。 |
| `debugging-and-error-recovery` | 用复现、定位、缩减、修复、回归防护的流程做标准调试。 |
| `deprecation-and-migration` | 处理旧系统下线、迁移、兼容期和切换策略。 |
| `documentation-and-adrs` | 记录架构决策、发布说明和长期需要保留的上下文。 |
| `frontend-ui-engineering` | 落地生产级 UI、组件、布局、交互和可访问性。 |
| `git-workflow-and-versioning` | 处理分支、提交、冲突、版本化和变更组织。 |
| `idea-refine` | 把模糊想法收敛成更清晰的目标、方向和约束。 |
| `incremental-implementation` | 把较大的实现拆成渐进式、可验证的小切片。 |
| `performance-optimization` | 做性能分析、瓶颈定位和优化。 |
| `planning-and-task-breakdown` | 在需求已较清晰时拆任务、排序依赖、写验收标准。 |
| `security-and-hardening` | 处理输入校验、鉴权、密钥、依赖风险和硬化。 |
| `shipping-and-launch` | 做上线前检查、灰度、监控和回滚准备。 |
| `source-driven-development` | 先查官方文档，再按权威来源实现和引用。 |
| `spec-driven-development` | 在编码前先补规格、边界、验收条件。 |
| `test-driven-development` | 用测试驱动实现或修复，并补回归保护。 |

## Managed: extra-skills

> Source: `extra-skills/` — 3 skills, fully managed.

| Skill | 用途 |
| --- | --- |
| `agent-browser` | 做通用浏览器自动化，适合外部网站或需要真实交互流程的场景。 |
| `frontend-design` | 生成有明确视觉方向、避免 AI 套路感的高质量页面和组件。 |
| `webapp-testing` | 用 Playwright 验证本地 Web 应用，适合 UI 流程、截图、日志和回归检查。 |

## Platform-Native Skills

> Source: Host platform runtime (e.g. `~/.gemini/antigravity/skills/`). Not version-managed by this repo. The descriptions below are for routing reference only.

| Skill | 用途 | 路由角色 |
| --- | --- | --- |
| `brainstorming` | 在创意型或需求不完整的任务里先做设计澄清和方案选择。 | 页面生成前置辅助；架构分析前置澄清 |
| `find-skills` | 当本地技能不够或用户想扩展能力时，帮助发现和安装新 skill。 | 仅在能力缺口时触发 |
| `mcp-builder` | 构建 MCP server、工具接口和协议层时使用。 | 架构分析条件辅助 |
| `planning-with-files-zh` | 为长任务、多步骤任务、跨会话任务建立持久化规划文件。 | 文件规划主路由 |
| `senior-fullstack` | 提供通用全栈脚手架和分析能力。 | **非默认**；仅在用户明确要广域 bootstrap 时使用 |
| `systematic-debugging` | 以"先根因、后修复"为硬约束的调试协议。 | 调试主路由（与 `debugging-and-error-recovery` 互斥） |
| `vercel-react-best-practices` | 在 React / Next.js 项目中套用 Vercel 的性能和实现最佳实践。 | 页面生成条件辅助 |

## Deprecated

| Skill | 状态 | 说明 |
| --- | --- | --- |
| `using-agent-skills` | ⛔ DEPRECATED | 原有 meta-skill，职责已被 `skill-suite-orchestrator` 完全接管。保留仅用于维护 skill suite 自身时的参考。不参与任何任务的默认路由。 |

## Default Exclusions

- `plugins/` 下的 skill 不纳入默认路由面，除非用户明确要求插件工作流。
- `senior-fullstack` 不作为默认首选，因为它过于宽泛，不符合"最小必要集"原则。
- Deprecated skills 不参与路由。
