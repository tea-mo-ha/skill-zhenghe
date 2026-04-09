# Routing Matrix

Use this matrix to turn user intent into the smallest sufficient subskill set. Always choose one dominant scenario first, then add only the directly relevant helpers.

## Global Rules

- Default target: 1 primary skill plus 0-2 supporting skills.
- If one skill is enough, do not add another.
- Do not attach helper skills on speculation or "just in case."
- Add a supporting skill only when the task has an explicit unmet requirement that the primary skill does not cover.
- Hard ceiling: avoid more than 4 skills unless the user explicitly asks for an end-to-end, cross-phase workflow.
- Never enable all browser skills together.
- Never enable all debugging skills together.
- Never pull in `senior-fullstack` by default.
- Treat `using-agent-skills` as a meta-skill and exclude it from normal default routing.

## 1. 审核项目

**Primary route**

- `code-review-and-quality`

**Add only when needed**

- `security-and-hardening`: 涉及鉴权、用户输入、密钥、外部服务、存储安全。
- `performance-optimization`: 涉及加载速度、Core Web Vitals、慢查询、N+1、渲染性能。
- `documentation-and-adrs`: 审核结果需要沉淀为 ADR、评审纪要、风险清单。
- `systematic-debugging` or `debugging-and-error-recovery`: 审核中已发现正在发生的错误，需要从 review 切到诊断。

**Intent -> chosen_subskills**

- “审核这个项目” -> `code-review-and-quality`
- “做一次安全审核” -> `code-review-and-quality`, `security-and-hardening`
- “评审这个项目的性能和质量” -> `code-review-and-quality`, `performance-optimization`

## 2. 架构分析

**Primary route selection**

- 默认优先级 -> `spec-driven-development` → `api-and-interface-design` → `planning-and-task-breakdown`
- 只有需求明显模糊、目标不成形、边界不清时，才在最前面加 `idea-refine` 或 `brainstorming`

**Add only when needed**

- `source-driven-development`: 方案强依赖框架或官方最佳实践。
- `documentation-and-adrs`: 需要沉淀架构决策。
- `planning-with-files-zh`: 任务很长、跨会话、跨阶段，需要持久化计划。
- `mcp-builder`: 目标本身就是 MCP server 或工具协议层。
- `senior-fullstack`: 用户明确要求全栈脚手架、技术栈基线或广域架构模板。

**Intent -> chosen_subskills**

- “分析这个架构” -> `spec-driven-development`, `api-and-interface-design`
- “帮我把这个想法收成可执行架构” -> `idea-refine`, `spec-driven-development`, `api-and-interface-design`
- “给这个方案拆任务” -> `spec-driven-development`, `api-and-interface-design`, `planning-and-task-breakdown`

## 3. 页面生成

**Primary route selection**

- 提到风格、视觉、参考图、品牌感、调性、版式方向 -> `frontend-design`
- 提到 React、组件、实现、落地、可运行代码 -> `frontend-ui-engineering`

**Add only when needed**

- `brainstorming`: 页面目标、风格、信息层级不清晰。
- `frontend-design`: 当主路由是 `frontend-ui-engineering`，但任务又明确要求强视觉方向或品牌表达。
- `frontend-ui-engineering`: 当主路由是 `frontend-design`，且任务要求实际落地成可运行界面代码。
- `vercel-react-best-practices`: 技术栈是 React / Next.js，且需要遵守现代实现模式。
- `api-and-interface-design`: 页面同时涉及接口契约、数据交互或前后端边界。
- `browser-testing-with-devtools` or `webapp-testing`: 页面完成后需要浏览器验证。

**Intent -> chosen_subskills**

- “做一个登录页” -> `frontend-design`, `frontend-ui-engineering`
- “做一个 Next.js 落地页并遵守最佳实践” -> `frontend-design`, `frontend-ui-engineering`, `vercel-react-best-practices`
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

- 默认不要同时启用 `systematic-debugging` 和 `debugging-and-error-recovery`。
- 先选一个；只有在验证阶段确认当前调试协议不足时，才切换或升级。

**Intent -> chosen_subskills**

- “修这个 bug” -> `systematic-debugging`, `test-driven-development`
- “CI 里这个测试挂了” -> `debugging-and-error-recovery`, `test-driven-development`
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

- `ci-cd-and-automation`: 需要改流水线、部署脚本、自动化门禁。
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
- 本地 skill 不够或用户想找新能力 -> `find-skills`

**Add only when needed**

- `idea-refine`: 规划之前目标仍然模糊。
- `spec-driven-development`: 先补规格再拆任务。
- `using-agent-skills`: 只在需要解释本地 skill 发现逻辑或维护 skill suite 时才用。

**Intent -> chosen_subskills**

- “帮我规划这个多步骤项目” -> `planning-with-files-zh`
- “把这个需求拆成任务” -> `planning-and-task-breakdown`
- “看看有没有现成 skill 能做这件事” -> `find-skills`

## Anti-Patterns

- 不要把“审核项目 + 架构分析 + 页面生成 + 调试修复 + 浏览器验证 + 上线”一次性全开。
- 不要在没有明确浏览器目标时同时启用 `webapp-testing`、`browser-testing-with-devtools`、`agent-browser`。
- 不要为了“保险”同时启用 `systematic-debugging` 和 `debugging-and-error-recovery`。
- 不要因为“可能有帮助”就附加 skill；一个 skill 够用时不要加第二个。
- 不要因为是大任务就默认启用 `senior-fullstack`。
