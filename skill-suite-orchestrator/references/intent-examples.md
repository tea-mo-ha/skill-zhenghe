# Intent Mapping Examples

> Version: 1.0.0 | Updated: 2026-04-27 | Load this file ONLY if you need concrete examples of how to map user prompts to `chosen_subskills`.

## 1. 审核项目 (project_review)
- “审核这个项目” -> `code-review-and-quality`
- “做一次安全审核” -> `code-review-and-quality`, `security-and-hardening`
- “评审这个项目的性能和质量” -> `code-review-and-quality`, `performance-optimization`

## 2. 架构分析 (architecture_analysis)
- “分析这个架构” -> `spec-driven-development`, `api-and-interface-design`, `planning-and-task-breakdown`
- “做最小架构路由验证” -> `spec-driven-development`, `api-and-interface-design`, `planning-and-task-breakdown`
- “先给简短 plan 的架构分析” -> `spec-driven-development`, `api-and-interface-design`, `planning-and-task-breakdown`
- “帮我把这个想法收成可执行架构” -> `idea-refine`, `spec-driven-development`, `api-and-interface-design`, `planning-and-task-breakdown`
- “给这个方案拆任务” -> `spec-driven-development`, `api-and-interface-design`, `planning-and-task-breakdown`

## 3. 页面生成 (page_generation)
- “设计一个登录页视觉方案” -> `frontend-design`
- “实现一个登录页组件” -> `frontend-ui-engineering`
- “为这个项目生成一个前端页面方案” -> `frontend-ui-engineering`, `api-and-interface-design`
- “做一个 Next.js 落地页并遵守最佳实践” -> `frontend-ui-engineering`, `vercel-react-best-practices`
- “先一起确定这个页面的方向再做” -> `brainstorming`, `frontend-design`

## 4. 调试修复 (debugging_repair)
- “修这个 bug” -> `systematic-debugging`
- “CI 里这个测试挂了” -> `debugging-and-error-recovery`
- “这个回归 bug 先补失败用例再修” -> `debugging-and-error-recovery`, `test-driven-development`
- “页面上这个交互有问题，帮我定位” -> `systematic-debugging`, `browser-testing-with-devtools`

## 5. 浏览器验证 (browser_validation)
- “帮我验证本地页面流程” -> `webapp-testing`
- “看一下这个页面的 console 和 network” -> `browser-testing-with-devtools`
- “去网站上帮我点一遍流程” -> `agent-browser`

## 6. 交付上线 (shipping_launch)
- “准备上线” -> `shipping-and-launch`
- “把这个功能安全上线并补 CI” -> `shipping-and-launch`, `ci-cd-and-automation`, `security-and-hardening`
- “这个发布还涉及旧系统迁移” -> `shipping-and-launch`, `deprecation-and-migration`

## 7. 文件规划与辅助技能发现 (planning_discovery)
- “帮我规划这个多步骤项目” -> `planning-with-files-zh`
- “把这个需求拆成任务” -> `planning-and-task-breakdown`
- “帮我给这个仓库新增一个 managed skill” -> `managed-skill-creator`
- “试试有没有现成 skill 能做这件事” -> `find-skills`

## 8. 全自动工作流管线建设 (autonomous_pipeline)
- “帮我构建或重构这套管线系统的全自动流” -> `agency-agents-orchestrator`
