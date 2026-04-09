# Skill Inventory

This inventory covers the real skills currently available under `addy-skills`, `extra-skills`, and `copied-existing-skills`. Use it as the authoritative local catalog for routing.

## addy-skills

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

## extra-skills

| Skill | 用途 |
| --- | --- |
| `agent-browser` | 做通用浏览器自动化，适合外部网站或需要真实交互流程的场景。 |
| `frontend-design` | 生成有明确视觉方向、避免 AI 套路感的高质量页面和组件。 |
| `webapp-testing` | 用 Playwright 验证本地 Web 应用，适合 UI 流程、截图、日志和回归检查。 |

## copied-existing-skills

| Skill | 用途 |
| --- | --- |
| `brainstorming` | 在创意型或需求不完整的任务里先做设计澄清和方案选择。 |
| `find-skills` | 当本地技能不够或用户想扩展能力时，帮助发现和安装新 skill。 |
| `mcp-builder` | 构建 MCP server、工具接口和协议层时使用。 |
| `planning-with-files-zh` | 为长任务、多步骤任务、跨会话任务建立持久化规划文件。 |
| `senior-fullstack` | 提供通用全栈脚手架和分析能力；只在用户明确要广域 bootstrap 或通用 fullstack 套件时使用。 |
| `systematic-debugging` | 以“先根因、后修复”为硬约束的调试协议。 |
| `vercel-react-best-practices` | 在 React / Next.js 项目中套用 Vercel 的性能和实现最佳实践。 |

## Meta-skills

| Skill | 用途 |
| --- | --- |
| `using-agent-skills` | 原有 meta-skill。仅在解释 skill 发现逻辑、比较技能边界、或维护 skill suite 本身时参考，不参与普通任务默认路由。 |

## Default Exclusions

- `plugins/` 下的 skill 不纳入默认路由面，除非用户明确要求插件工作流。
- `using-agent-skills` 已降级为 meta-skill，不参与普通任务默认路由，因为 `skill-suite-orchestrator` 已接管总控职责。
- `senior-fullstack` 不作为默认首选，因为它过于宽泛，不符合“最小必要集”原则。
