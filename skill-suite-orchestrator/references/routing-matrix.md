# Routing Matrix

> Version: 1.4.0 | Updated: 2026-04-17 | Human-readable intent → skill mapping. Final governed-route normalization lives in `route-profiles.yaml`.

Use this matrix to turn user intent into the smallest sufficient subskill set. Always choose one dominant scenario first, then add only the directly relevant helpers.

**Skill provenance**: This matrix routes to both **managed skills** (version-controlled in this repo under `addy-skills/` and `extra-skills/`) and **platform-native skills** (provided by the host runtime). See `skill-inventory.md` for the authoritative source list and version governance rules.

**Normalization source**: For governed scenarios such as architecture analysis, page generation, and debugging repair, normalize the final `chosen_subskills` set against `route-profiles.yaml` before output. This matrix explains the intent model; `route-profiles.yaml` defines the final required / optional / forbidden / mutually-exclusive shape.

## Global Rules

- Default target: 1 primary skill plus 0-2 supporting skills.
- If one skill is enough, do not add another.
- Do not attach helper skills on speculation or "just in case."
- Add a supporting skill only when the task has an explicit unmet requirement that the primary skill does not cover.
- Hard ceiling: avoid more than 4 skills unless the user explicitly asks for an end-to-end, cross-phase workflow.
- Never include `skill-suite-orchestrator` itself in `chosen_subskills`; list only delegated downstream skills.
- Never include `skill-suite-orchestrator` itself in `chosen_subskills` in any scenario, without exception.
- Platform-native skills are conditional candidates only. Select them only when the current runtime confirms they are actually available.
- If a platform-native skill is unavailable at runtime, do not keep it in `chosen_subskills`; fall back to the nearest managed route or report the capability as unavailable.
- Never enable all browser skills together.
- Never enable all debugging skills together.
- Never pull in `senior-fullstack` by default.
- Use `context-engineering` when agent output quality degrades, context is stale, or a new session needs grounding.
- Do not route to plugin-owned or other external skills unless the user explicitly asks for them.
- Before selecting frontend debugging or browser validation, confirm the repository exposes a runnable app or UI surface, or that the user explicitly points to one.
- In non-app repositories, do not infer frontend bug-fixing or browser-validation routes from vague page or bug language.

## 1. 审核项目

**Primary route**

- `code-review-and-quality`

**Add only when needed**

- `security-and-hardening`: 涉及基础鉴权、用户输入、密钥、常规外部服务和存储安全验证。
- `agency-security-engineer`: 涉及最高安全红线审查、深层威胁建模分析、系统核心资产权限隔离时，且当前运行时确认可用，才全面接管防御。
- `performance-optimization`: 涉及常见加载速度、Core Web Vitals、慢查询、常见N+1等常规渲染性能。
- `agency-performance-benchmarker`: 怀疑存在深层性能雪崩隐患、复杂并发卡死、或需要全盘接管极限压测验证架构时，且当前运行时确认可用。
- `documentation-and-adrs`: 审核结果需要沉淀为 ADR、评审纪要、风险清单。
- `systematic-debugging` or `debugging-and-error-recovery`: 审核中已发现正在发生的错误，需要从 review 切到诊断。

**Intent -> chosen_subskills**

- “审核这个项目” -> `code-review-and-quality`
- “做一次安全审核” -> `code-review-and-quality`, `security-and-hardening`
- “评审这个项目的性能和质量” -> `code-review-and-quality`, `performance-optimization`

## 2. 架构分析

**Primary route selection**

- 默认必须委派 -> `spec-driven-development` → `api-and-interface-design` → `planning-and-task-breakdown`
- 该场景的最终归一化规则由 `route-profiles.yaml::architecture_analysis` 定义
- “最小架构路由验证”“dry run”“只给简短 plan”“先做一个短版架构判断” 仍然归到同一条强制链路
- 即使用户只要简短输出，也不要因为输出更短而省掉 `planning-and-task-breakdown`
- 除非仓库中明显不存在可分析的规格、接口或设计边界，否则不要跳过前两个。
- 只有需求明显模糊、目标不成形、边界不清时，才在最前面加 `idea-refine` 或 `brainstorming`

**Add only when needed**

- `source-driven-development`: 方案强依赖框架或官方最佳实践。
- `agency-software-architect`: 遇到全局系统级领域建模（DDD）、极度复杂的跨域混合系统整合设计时，且当前运行时确认可用。
- `agency-backend-architect`: 面临高吞吐量的核心后端重构、大型微服务体系结构拆分或数据库大并发核心建模工作时，且当前运行时确认可用。
- `documentation-and-adrs`: 需要沉淀架构决策。
- `planning-with-files-zh`: 任务很长、跨会话、跨阶段，需要持久化计划。
- `mcp-builder`: 目标本身就是 MCP server 或工具协议层。
- `senior-fullstack`: 用户明确要求全栈脚手架、技术栈基线或广域架构模板。

**Intent -> chosen_subskills**

- “分析这个架构” -> `spec-driven-development`, `api-and-interface-design`, `planning-and-task-breakdown`
- “做最小架构路由验证” -> `spec-driven-development`, `api-and-interface-design`, `planning-and-task-breakdown`
- “先给简短 plan 的架构分析” -> `spec-driven-development`, `api-and-interface-design`, `planning-and-task-breakdown`
- “帮我把这个想法收成可执行架构” -> `idea-refine`, `spec-driven-development`, `api-and-interface-design`, `planning-and-task-breakdown`
- “给这个方案拆任务” -> `spec-driven-development`, `api-and-interface-design`, `planning-and-task-breakdown`

## 3. 页面生成

**Primary route selection**

- 页面生成默认只允许从以下本地 skill 中选择：`frontend-design`、`frontend-ui-engineering`、`api-and-interface-design`、`vercel-react-best-practices`、`brainstorming`
- 提到风格、视觉、参考图、品牌感、调性、版式方向 -> `frontend-design`
- 提到 React、组件、实现、页面结构、落地、可运行代码 -> `frontend-ui-engineering`
- 如果仓库明显不是 app 型仓库，且用户没有给出真实页面入口、组件入口或运行目标，不要掉进前端 bug 修复或浏览器验证路线；保持在设计或规划路由。
- 不要逃逸到未在本地矩阵中声明的外部插件 skill，例如 `build-web-apps:frontend-skill`，除非用户明确要求使用外部插件能力。

**Add only when needed**

- `brainstorming`: 页面目标、风格、信息层级不清晰时，才作为前置辅助。
- `frontend-design`: 当主路由是 `frontend-ui-engineering`，但任务又明确要求强视觉方向或品牌表达。
- `frontend-ui-engineering`: 当主路由是 `frontend-design`，且任务要求实际落地成可运行界面代码。
- `vercel-react-best-practices`: 技术栈是 React / Next.js，且需要遵守现代实现模式。
- `api-and-interface-design`: 页面同时涉及接口契约、数据交互或前后端边界。
- `browser-testing-with-devtools` or `webapp-testing`: 页面完成后需要浏览器验证。

**Intent -> chosen_subskills**

- “设计一个登录页视觉方案” -> `frontend-design`
- “实现一个登录页组件” -> `frontend-ui-engineering`
- “为这个项目生成一个前端页面方案” -> `frontend-ui-engineering`, `api-and-interface-design`
- “做一个 Next.js 落地页并遵守最佳实践” -> `frontend-ui-engineering`, `vercel-react-best-practices`
- “先一起确定这个页面的方向再做” -> `brainstorming`, `frontend-design`

## 4. 调试修复

**Primary route selection**

- `systematic-debugging`: 根因不清、跨层联动、已经尝试过多次、存在错误修错风险时使用。
- `debugging-and-error-recovery`: 标准的测试失败、构建失败、运行时错误，且故障面较清晰时使用。

**Add only when needed**

- `test-driven-development`: 需要先补失败用例或给修复加回归保护。
- `code-simplification`: 修完后还要顺手降低复杂度，但不能扩大改动面。
- `browser-testing-with-devtools` or `webapp-testing`: 前端问题需要真实浏览器复现或回归。

**Boundary rule**

- 默认不得同时启用 `systematic-debugging` 和 `debugging-and-error-recovery`。
- 永远不要在同一个默认路由里同时委派这两个调试 skill。
- 先选一个；只有在验证阶段确认当前调试协议不足时，才切换或升级。
- 如果仓库不是 app 型仓库，不要把模糊的页面或 UI 任务误判成前端 bug 修复路线，除非用户明确指向真实页面或交互入口。

**Intent -> chosen_subskills**

- “修这个 bug” -> `systematic-debugging`
- “CI 里这个测试挂了” -> `debugging-and-error-recovery`
- “这个回归 bug 先补失败用例再修” -> `debugging-and-error-recovery`, `test-driven-development`
- “页面上这个交互有问题，帮我定位” -> `systematic-debugging`, `browser-testing-with-devtools`

## 5. 浏览器验证

**Choose exactly one primary browser skill**

- `webapp-testing`: 本地 Web 应用、Playwright 回归、截图、日志。
- `browser-testing-with-devtools`: 需要 console、network、DOM、performance 现场检查。
- `agent-browser`: 需要通用浏览器自动化，尤其是外部网站或真实流程操作。

**Add only when needed**

- `frontend-ui-engineering`: 浏览器验证后立刻要做 UI 修复。
- `test-driven-development`: 要把浏览器问题固化为自动化回归。

**Intent -> chosen_subskills**

- “帮我验证本地页面流程” -> `webapp-testing`
- “看一下这个页面的 console 和 network” -> `browser-testing-with-devtools`
- “去网站上帮我点一遍流程” -> `agent-browser`

## 6. 交付上线

**Primary route**

- `shipping-and-launch`

**Add only when needed**

- `ci-cd-and-automation`: 需要改常规流水线、简单部署脚本、常规阶段的自动化门禁。
- `agency-devops-automator`: 需要对整个部署管线基建、云资源全自动化配置做重构转型，或打造最高标准 CI/CD Pipeline 时，且当前运行时确认可用。
- `agency-sre-site-reliability-engineer`: 上线涉及最核心链路 SLO 以及熔断保护、需要设计极高可用性、强抗灾能力的维稳架构时，且当前运行时确认可用。
- `git-workflow-and-versioning`: 需要整理分支、提交、发版或版本控制动作。
- `deprecation-and-migration`: 上线伴随旧路径下线、灰度迁移或替换策略。
- `documentation-and-adrs`: 需要补上线说明、运维说明、ADR 或变更记录。
- `security-and-hardening`: 上线门禁集中在安全。
- `performance-optimization`: 上线门禁集中在性能。

**Intent -> chosen_subskills**

- “准备上线” -> `shipping-and-launch`
- “把这个功能安全上线并补 CI” -> `shipping-and-launch`, `ci-cd-and-automation`, `security-and-hardening`
- “这个发布还涉及旧系统迁移” -> `shipping-and-launch`, `deprecation-and-migration`

## 7. 文件规划与辅助技能发现

**Primary route selection**

- 长任务、多阶段、跨会话、需要持久化状态 -> `planning-with-files-zh`
- 需求清楚但要拆实施任务 -> `planning-and-task-breakdown`
- 明确要新增或更新本仓库 managed skill -> `managed-skill-creator`
- 本地 skill 不够或用户想找新能力 -> `find-skills`

**Add only when needed**

- `idea-refine`: 规划之前目标仍然模糊。
- `spec-driven-development`: 先补规格再拆任务。
- `context-engineering`: 新会话上下文缺失、跨会话恢复、或输出质量下降时用于重建上下文。

**Intent -> chosen_subskills**

- “帮我规划这个多步骤项目” -> `planning-with-files-zh`
- “把这个需求拆成任务” -> `planning-and-task-breakdown`
- “帮我给这个仓库新增一个 managed skill” -> `managed-skill-creator`
- “把这个现有 skill 重写并接入默认路由” -> `managed-skill-creator`
- “试试有没有现成 skill 能做这件事” -> `find-skills`

## 8. 全自动工作流管线建设

**Primary route**

- `agency-agents-orchestrator`

**Add only when needed**

- 此主路由本身即为应对顶级流程与复杂生态。如果其管线涉及到细分的重核能力，在后续阶段交由其他大拿接管。

**Intent -> chosen_subskills**

- “帮我构建或重构这套管线系统的全自动流” -> `agency-agents-orchestrator`
- 如果 `agency-agents-orchestrator` 在当前运行时不可用，改走 `planning-with-files-zh` 或 `planning-and-task-breakdown` 做受限降级，并明确告知“自动化主路由当前不可用”。

## Anti-Patterns

- 不要把“审核项目 + 架构分析 + 页面生成 + 调试修复 + 浏览器验证 + 上线”一次性全开。
- 不要把 `skill-suite-orchestrator` 自己写进 `chosen_subskills`。
- 不要把外部插件 skill 写进页面生成场景的默认 `chosen_subskills`。
- 不要在没有明确浏览器目标时同时启用 `webapp-testing`、`browser-testing-with-devtools`、`agent-browser`。
- 不要为了“保险”同时启用 `systematic-debugging` 和 `debugging-and-error-recovery`。
- 不要因为“可能有帮助”就附加 skill；一个 skill 够用时不要加第二个。
- 不要因为是大任务就默认启用 `senior-fullstack`。
- 不要在非 app 型仓库里默认走前端 bug 修复或浏览器验证路线。
