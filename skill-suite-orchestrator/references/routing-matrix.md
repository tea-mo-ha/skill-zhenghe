# Routing Matrix

> Version: 2.0.0 | Updated: 2026-04-27 | Compact scenario mapper. For strict normalization rules, read `route-profiles.yaml`.

This matrix helps map user intent to the dominant scenario. Once the scenario is identified, use `route-profiles.yaml` to determine the exact required, optional, and mutually exclusive skills.

## Scenario Mapping

| 场景 (Scenario) | 适用情况 (When to use) | 主路由 (Primary Route) |
|---|---|---|
| **1. 审核项目 (project_review)** | 代码评审、质量检查、安全审计、性能评估。 | `code-review-and-quality` |
| **2. 架构分析 (architecture_analysis)** | 系统设计、API设计、任务拆解、MVP规划、技术选型。 | `spec-driven-development` → `api-and-interface-design` → `planning-and-task-breakdown` |
| **3. 页面生成 (page_generation)** | 前端页面、组件开发、视觉设计、UI落地。 | `frontend-design` 或 `frontend-ui-engineering` |
| **4. 调试修复 (debugging_repair)** | 修bug、查报错、修复CI失败、测试失败。 | `systematic-debugging` 或 `debugging-and-error-recovery` |
| **5. 浏览器验证 (browser_validation)** | 本地网页测试、DevTools检查、外部网站自动化。 | `webapp-testing` 或 `browser-testing-with-devtools` |
| **6. 交付上线 (shipping_launch)** | 发布准备、部署脚本、灰度迁移、CI/CD配置。 | `shipping-and-launch` |
| **7. 文件规划与发现 (planning_discovery)** | 复杂多步长任务规划、寻找未知skill、创建managed skill。 | `planning-with-files-zh` 等 |
| **8. 自动管线建设 (autonomous_pipeline)** | 构建多智能体工作流、CI大管线编排。 | `agency-agents-orchestrator` |

## On-Demand Details
If you are unsure how to map a specific user intent to subskills for a scenario, read `references/intent-examples.md` for concrete few-shot examples. DO NOT load `intent-examples.md` if the mapping is obvious.

## Anti-Patterns

- 不要同时开启多个主场景的技能。
- 不要为了“保险”随意添加辅助 skill。一个 skill 够用时不要加第二个。
- 详情请查阅 `route-profiles.yaml` 中的 `mutually_exclusive` 和 `forbidden` 规则。
