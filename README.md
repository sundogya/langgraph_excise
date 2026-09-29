# LangGraph 7 天生产级（中级偏上）实战特训计划

本计划针对有一定 Python 基础与 LLM API 调用经验的开发者，通过每天 5~6 小时的高强度、沉浸式编码与架构推演，帮助你在 **7 天内** 具备在真实业务中独立设计、开发和调优复杂 LangGraph 智能体系统的能力。

---

## 📅 总体时间表概览

- **Day 1：底座重构** —— 有限状态机（FSM）模型、State Schema、Reducer 与极速线性图
- **Day 2：核心闭环** —— 条件边路由、Tool Calling 循环（ReAct 架构）与原生手写状态接管
- **Day 3：生产级持久化** —— Checkpointer（内存与持久化后端）、`thread_id` 会话管理与 Time Travel
- **Day 4：精细控制与人工介入** —— Human-in-the-loop（挂起、审批、状态修改与断点续传）
- **Day 5：Agentic RAG 实战** —— Adaptive / Corrective RAG 架构、混合检索、Rerank 与质量评分节点
- **Day 6：多智能体与高阶拓扑** —— Subgraphs（子图）、Supervisor 路由模式与并发分支（Fan-out/Fan-in）
- **Day 7：工程化落地与线上调优** —— 流式输出（Streaming）、LangSmith 追踪、Ragas 自动化评测与上线防坑

---

## 🚀 每日详细执行大纲

### Day 1：底座重构 —— 掌握 LangGraph 的核心心智模型
* **核心目标**：彻底告别盲目套壳，建立状态机（FSM）思维，理解数据流在图中的演进。
* **学习要点**：
  1. **状态定义**：学习使用 `TypedDict` 与 `Pydantic` 定义强类型 State。
  2. **Reducer 机制**：理解如何使用 `Annotated[list, operator.add]` 实现状态增量合并，避免无意覆盖。
  3. **基础拓扑**：手写 `StateGraph`，添加节点（Node）、边（Edge），编译（compile）并运行最简单的 3 节点线性工作流。
* **实战练习**：
  - 编写一个“文本清洗 $\to$ 情感分析 $\to$ 摘要生成”的线性 Pipeline 图，确保每个节点正确返回 State 增量。

---

### Day 2：核心闭环 —— Tool Calling 与原生 ReAct 架构
* **核心目标**：不依赖黑盒封装，亲手用状态图实现具备自主决策和工具循环能力的智能体。
* **学习要点**：
  1. **大模型绑定**：使用 OpenAI / Anthropic 的原生 Tool Calling 或 `bind_tools`。
  2. **条件边（Conditional Edge）**：根据 LLM 的输出（是否包含 `tool_calls`）分流到 `ToolNode` 或 `END`。
  3. **循环死锁防范**：理解 ReAct 循环的终止条件与最大步数限制（Max Steps）设计。
* **实战练习**：
  - 手写一个包含“网页搜索 (Mock) + 计算器”的 ReAct Agent 图，观察并打印每一次状态迭代的全过程。

---

### Day 3：生产级持久化 —— Checkpointer 与多会话管理
* **核心目标**：赋予智能体“长期记忆”与生产级容灾能力，理解分布式会话架构。
* **学习要点**：
  1. **MemorySaver 与持久化**：配置 `MemorySaver`（内存级）以及接入 SQLite / PostgreSQL 的 Checkpointer。
  2. **会话隔离**：理解 `config={"configurable": {"thread_id": "xxx"}}` 如何隔离不同用户的上下文。
  3. **Time Travel（时间旅行）**：利用 `graph.get_state_history()` 获取历史检查点，并实现状态回滚或分支复活。
* **实战练习**：
  - 开发一个多用户多轮对话聊天机器人，支持中途重启服务后通过 `thread_id` 完美恢复历史状态。

---

### Day 4：精细控制与人工介入 —— Human-in-the-loop (HITL)
* **核心目标**：攻克企业级落地最大的痛点——让大模型在关键决策前“听人类指挥”。
* **学习要点**：
  1. **编译期断点**：掌握 `interrupt_before` 与 `interrupt_after` 的使用场景。
  2. **动态中断**：理解运行时动态 `interrupt()` 挂起。
  3. **状态注入与修改**：学会在人工审批拒绝或修改输入后，使用 `Command(update=...)` 或 `update_state` 恢复图的执行。
* **实战练习**：
  - 构建一个“电商退款审批 Agent”：当退款金额大于 200 元时自动触发图挂起，等待人工审核（同意/拒绝/修改金额）后再往下执行。

---

### Day 5：Agentic RAG 实战 —— 动态检索与自我反思
* **核心目标**：从Naive RAG 跃迁到 Agentic RAG，解决传统检索“召回率低、幻觉多”的硬伤。
* **学习要点**：
  1. **混合检索与重排**：结合 Vector Search + BM25，并引入 BGE-Reranker。
  2. **Adaptive RAG 路由**：设计判断节点，自主决定是走直接闲聊、内部知识库检索还是外网搜索。
  3. **Self-RAG / Corrective RAG**：设计文档质量打分节点（Grade Documents），若检索文档不相关则触发 Query 改写并重新检索。
* **实战练习**：
  - 落地一个带有“Query 改写 $\to$ 混合检索 $\to$ 文档相关性过滤 $\to$ 生成 $\to$ 幻觉校验”的闭环高可靠企业知识库检索 Agent。

---

### Day 6：多智能体与高阶拓扑 —— Subgraphs 与 Supervisor
* **核心目标**：应对复杂业务场景，学会将单体臃肿的图拆分为模块化、可协作的多智能体网络。
* **学习要点**：
  1. **子图（Subgraphs）嵌套**：将特定领域的功能封装为独立子图，实现状态隔离与复用。
  2. **Supervisor 架构**：中央调度器节点根据用户意图，动态指派专业子 Agent（如：研究员、代码员、评审员）。
  3. **并发分支（Fan-out / Fan-in）**：实现多个子任务并行执行，并在合并节点处理冲突。
* **实战练习**：
  - 搭建一个“自动化竞品分析助手”：Supervisor 收到任务后，并发分发给“市场检索 Agent”和“财报分析 Agent”，最后由“综合报告生成 Agent”汇总。

---

### Day 7：工程化落地与线上调优 —— 观测、评测与上线防坑
* **核心目标**：打通从“本地跑通”到“生产部署”的最后一公里，确保系统具备可观测、高稳定、可量化指标。
* **学习要点**：
  1. **流式输出（Streaming）**：掌握 `astream(stream_mode="updates")` 与 `stream_mode="messages"`，实现流畅的打字机前端效果。
  2. **LangSmith 可观测性**：配置环境变量接入 LangSmith，查看每一步 Token 消耗、耗时与报错堆栈。
  3. **RAG 自动化评测**：使用 Ragas 针对知识库评测 Faithfulness（忠实度）和 Answer Relevance（相关度）。
* **实战练习**：
  - 将前几天开发的系统封装为 FastAPI 后端，支持 SSE 流式返回，并使用 LangSmith 完成一次完整的线上链路追踪排错。

---

## 🛠️ 高效通关的四个黄金法则

1. **拒绝“只看不写”**：每天 5 小时中，阅读文档/查阅资料控制在 1 小时内，剩余 4 小时务必在 IDE 中单步断点调试、打印 State 结构。
2. **善用 LangSmith 降维打击**：从 Day 1 开始就配好 LangSmith Key，把图运行的可视化界面常年挂在屏幕一侧，它是最好的代码调试器。
3. **状态克制原则**：设计 State Schema 时，只保留业务流转必须的字段，不要把所有大对象的临时变量全塞进 State 里。
4. **异常边界处理**：在调用 LLM 节点和 Tool 节点时，务必加上 `try-except` 并配合图的重试策略（Retry Policy），防止偶发的 API 超时导致整个图崩溃。
