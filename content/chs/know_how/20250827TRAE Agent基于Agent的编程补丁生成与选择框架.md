---
title: "2025-08-27 TRAE Agent 基于Agent的编程补丁生成与选择框架"
date: 2025-08-27T14:11:46.516235
tags: ['tech']
description: ""
---

最近几个月我都在使用Trae。它更新很频繁，中间经历了一次大改——Logo由橙色改为绿色，以及数不清的小版本迭代。基本上每天打开电脑TRAE都在提示更新。我挺好奇他们是怎么开发Agent的，最近就去看了他们的一些博客和论文。



Trae用的是agent-first架构。它的核心是Agent，而不是那种通用的聊天模型。也就是说，用户的查询会直接交给一个或一组最合适的Agent来处理。在Trae里，MCP不再直接和用户打交道，而是在底层发挥作用，就像Agent之间以及Agent和外部工具之间沟通和协调的“管道”或“神经系统”。

论文和博客里讲的都是怎么实现这个编程Agent的。具体来说：

- 真实场景中，修复缺陷往往涉及多个文件和模块，需要跨文件推理、感知上下文，并在整个代码库中验证补丁的正确性。Trae Agent研发了一种基于agent的集合推理框架，能够解决仓库级别的问题。
- Trae Agent的工作分为三个阶段：
![](https://uvidumfqwzk.feishu.cn/space/api/box/stream/download/asynccode/?code=YWIzOWViOTgwZDVmOThhYjIzYjU2YzMxMDI4ZWQzMzFfd3B5eVVSR2FRbzNxbldjcjhxbXhRWjc3WFZBblUyZmlfVG9rZW46RUlFd2JXUlkzb3FGZWZ4TFk0OWNJbkRSbkFiXzE3NTYzMDI3NTI6MTc1NjMwNjM1Ml9WNA)

（图源于论文：Trae Agent: An LLM-based Agent for Software  Engineering with Test-time Scaling ）

## 三个阶段对应三个Agent

- Coder Agent：并行生成候选补丁，通过提高温度和多模型轮询（如Gemini 2.5 Pro、Claude 3.7 Sonnet和GPT-4.1）来增加多样性。
- Tester Agent：自动提取并执行回归测试，过滤掉错误的补丁。
- Selector Agent：对剩余补丁进行仓库级静态和动态分析，通过投票选出最终补丁。




# 生态工具

TRAE建立了一个工具生态，包含以下四种工具，这些工具在三个阶段中都会被应用：

- 文件编辑工具：查看文件和目录结构，创建和编辑文件。
- Bash工具：提供持久的命令执行接口，让Agent能够与系统交互，捕获输出和错误信息。
- 顺序思考工具：将复杂问题拆解，进行迭代式思考和修正，提出假设并验证，提供结构化的问题解决和分析能力。
- 任务完成工具：发出任务结束信号，给出最终结果和总结。
# 阶段一：补丁生成

这个阶段主要是采用多个主流大语言模型根据描述生成候选补丁。这个阶段主要由Coder Agent完成，它遵循以下多步流程：

1. 分析问题描述，理解要解决的问题是什么；
1. 探索代码库，定位与问题相关的文件；
1. 复现 bug，验证其表现；
1. 通过代码审查诊断根本原因；
1. 生成代码补丁以修复已识别的缺陷；
1. 重新运行复现测试，验证补丁的正确性；
1. 总结整个工作流程，模拟真实的commit message。
为了增加候选结果的多样性，采取了以下措施：

1. 在运行Coder Agent时提高温度，增加多样性。
1. 引入Mixture设置，以轮询方式调用三种LLM生成补丁。
此外，为了实现可观测性，轨迹记录系统会详细记录每一步的信息，包括与LLM的交互、Agent的具体步骤、元数据以及错误追踪。

# 阶段二：补丁修剪

这个阶段由Tester Agent完成，它会自动从原始项目代码库中检索与问题描述相关的回归测试，并过滤掉不正确的补丁。具体做法如下：

1. 使用Python的unidiff库实现补丁解析器，将原始补丁转换为结构化表示。
1. 通过补丁归一化移除语义无关的元素，如多余空格、换行和注释。
1. 无法解析的补丁被视为无效并直接丢弃。
1. 对归一化后的补丁进行等价检测，若多条候选补丁的归一化结果完全相同，则判定其语义等价，仅保留其一。
## 阶段三：补丁选择

这个阶段由Selector Agent完成，它会进行以下操作：

1. 基于语法的投票：Selector agent 首先执行基于语法的投票，通过对候选补丁进行语法等价聚类，并选择出现频率最高的聚类作为潜在解决方案。其原理是，如果多个 Coder agent 独立生成了严格语法等价的补丁，则表明存在强烈共识，暗示这些高度一致的补丁更有可能是正确的
1. 多重选择投票：先对补丁进行去重。然后多个selector agent对去重后的补丁进行投票，选出最可能正确的补丁。如果票数分布均匀会增加投票轮数。
## 如何评估TRAE Agent：

TRAE Agent的性能通过与四种最新的集成推理基线方法（Augment、Augment w/ Pruning、DeiBase和DeiBase w/ Pruning）在三种主流LLM（Gemini 2.5 Pro、Claude 3.7 Sonnet和GPT-4.1）上进行对比评估。评估指标包括：

1. Oracle（理想情况）：只要N个候选补丁中存在正确补丁，就能选到它，体现最佳性能。
1. Adversary（对抗情况）：只有当全部N个候选补丁都正确时，才视为问题被解决，体现最差性能。
1. Average（平均情况）：从N个候选补丁中随机选取一个补丁时的期望性能。
然后计算pass@1。

## Benchmark

1. SWE-bench：来自12个流行的Python仓库，最初包含2,294个问题实例，通过收集GitHub上的Issue-Pull Request对构建。
1. SWE-bench Verified：OpenAI去年8月发布的包含500条经过人工验证的数据，这些数据从原始的SWE-bench数据集中筛选出来，经过人工标注和验证，确保数据的质量和可靠性，目前是SWE Benchmark的主流。
# 其他

1. Augment：基于“LLM 作为裁判”范式的提示式集成方法。通过提示 LLM 将每条候选补丁与问题描述进行比较，并选出最佳匹配。
1. DeiBase：提示 LLM 为每条候选补丁生成详细理由并给出置信度评分，最终选取评分最高的补丁作为最终方案。
1. Agentless是一个开源的大语言模型驱动框架，专门针对SWE-Bench基准测试。用 Agentless 框架可以在 SWE-Bench（Lite 或 Verified）上完整复现并提交补丁结果。感兴趣的可以去看：https://github.com/OpenAutoCoder/Agentless/blob/main/README_swebench.md
 