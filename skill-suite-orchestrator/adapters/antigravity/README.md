# Antigravity Adapter

这个目录把 `skill-suite-orchestrator` 包装成一个适合反重力使用的单入口适配层，同时继续复用现有核心逻辑。

## 目标

- 对反重力暴露一个稳定入口
- 继续复用 [../../SKILL.md](../../SKILL.md) 的主调度协议
- 继续复用 [../../references/routing-matrix.md](../../references/routing-matrix.md) 的路由策略
- 继续复用 [../../references/skill-inventory.md](../../references/skill-inventory.md) 的真实 skill 清单
- 不复制所有子 skill 内容
- 不修改 Codex 与反重力共享的核心逻辑

## 文件

- `manifest.json`: 机器可读适配描述，定义单入口定位、场景、输入输出契约、子 skill 来源和最小必要集原则
- `entry.md`: 反重力入口说明，定义进入时的操作顺序和输出格式
- `README.md`: 本说明文件

## 使用方式

反重力应把 `entry.md` 视为统一入口说明，把 `manifest.json` 视为适配元数据。

推荐调用语义：

1. 读取用户任务
2. 识别主意图
3. 依据核心 orchestrator 逻辑选择最小必要 skill 集
4. 输出 `chosen_subskills`
5. 再输出 `plan`、`execution`、`validation`

## 维护原则

- 改核心路由时，只更新上层引用的核心文件，不在这里复制一份
- 改反重力入口表现时，只调整本目录文件
- 适配层应始终保持“薄封装”，避免与核心逻辑分叉
