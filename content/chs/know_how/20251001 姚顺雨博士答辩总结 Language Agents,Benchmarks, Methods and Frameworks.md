---
title: "2025-10-01 姚顺雨博士答辩总结 Language Agents_Benchmarks, Methods and Frameworks"
date: 2025-10-01T14:11:50.876297
tags: ['tech']
description: ""
---

不得不感叹互联网真是太好了。近期在看一些 Agent 领域的论文时，发现无论如何都绕不开ReAct这个框架——它如此简洁，却又如此有效，真正体现了“大道至简”的思想。我在YouTube上找到了ReAct的作者Yao Shunyu的博士答辩。非常感谢这种无私的分享，让我获得了一次极其宝贵的学习机会。



视频链接：https://www.youtube.com/watch?v=zwfE6J2BIR4

注：文中所有的图都来自上面视频链接，文中不再注明

# 概览

Agent：

- Rule-based agents: manual design 人工写规则
- Learning-based agents: trial-and-error 靠试错学习
- Language agents: reasoning to act 先用语言推理，再行动
Environment：

- Interact with humans/physical world 与人交互
- Interact with games/simulation 与游戏交互
- Interact with the digital world (Internet) 与互联网交互
Challenges:

- Accessible methods for general agents
- Scalable benchmarks for practical tasks
主要的研究：

- Part 1: Benchmarking agents via digital automation
- Part 2: Building language agents that reason to act
- Part 3: Principled framework for language agents
# Part 1 Benchmarking agents via digital automation

Digital automation: tasks on the computer (写论文、跑实验、找文献、回邮件、debug、甚至和审稿人吵架) ，所有在电脑上能做的任务都可以被 automated，这叫 digital automation。

- Tremendous practical values, but little progress (think about Siri) 有很大的价值，但是进展有限。
- Underlying research challenges: （所以有两点挑战：1. 基于真实世界的推理 2. 在开放环境中做长期决策）
- 解决这些对 robot navigation, planning, coordination 都很重要
不包含这些 digital automation 的 agent benchmarks 有 MiniWoB, TextWorld, BabyAI。它们的共同特点是 simulation environment, small action space, synthetic text and short-horizon tasks。

## Webshop

WebGPT： 输入一个问题，经过网页浏览器之后，得到一些输出，需要通过 professional annotators 标注才能知道哪些是对的，哪些是错的，才能有 reward。

Desired benchmark: 针对 complex environment 的 research challenges，但是重要的是有 automatic reward function。

所以开发了 Webshop，用户可以通过对话来买东西。它满足上面的条件：

1. Large scale complex environment based on 1.16M
1. Automatic reward based on instruction and product attribute matching
1. Challenges language and visual understanding, and decision making
结果： 不管他们基于什么模型构建的 agent，性能（28.7%）还是达不到人类的一半。（模型有 Pre-trained image model (ResNet），Pre-trained language model (BERT, BART），imitation learning 和 reinforcement learning。

Imitation learning 是指让智能体照着人类做。

- 先收集人类专家完成任务的数据，通常是状态和动作。
- 然后用监督学习去拟合一个策略，复制人类行为。
- 训练完成后，智能体遇到新状态 s，就像人类那样直接输出动作 a。
Insight：

1. RL agent 的轨迹长度是 4.5，但是人类在这个任务上是 11.3，agent 不具有 long-horizon 的能力。
1. Webshop enables sim-to-real transfer。模拟→现实迁移（sim-to-real transfer）是指在 WebShop 这个模拟购物网站里训练好的语言智能体，不做任何额外微调，直接搬到真正的 Amazon、eBay 等真实网站上运行，仍能取得一定的成功率。
从 WebShop 开始，有大量的类似的 web interaction 的项目出现，探索 visual understanding, language understanding, decision making, planning, reinforcement learning 等方法。同时谷歌和 OpenAI 等也在这方面做了工业上的尝试。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251001/a460b60c.png)

这个时候，Coding 的 benchmarks 也开始流行，例如 HumanEval，它的任务比较简单，只需要几行代码就能完成。在短短两年内，各路模型和系统将它的正确率从 25% 推到 95%。这个任务目前来说太简单了。

然后就有了 SWE-Bench。它的任务更难，输入是一个 GitHub repo 和 issue，输出是一个来解决这些 issue 的 file diff，它用 unit tests 来进行评估。

但是，仅仅依靠依靠大语言模型 sequence-to-sequence 的设置，不能解决 SWE-Bench 的难题。这里进行了一个测试，ChatGPT-3.5 解决了 0.2% 的问题，Claude 2 能解决 1.96%。

## 总结

1. Digital Automation is a new frontier for autonomous agents，它有巨大的价值，有 scalable environment，但是瓶颈在于 scalable evaluation。
1. Digital Automation 需要的是开放性语言环境下的连续决策（比如写代码、找论文、回邮件、debug、跑实验等），但是 LLM 和 RL agents 都不能完成这个任务，因此需要一种新型的 agents。
# Part 2 Building language agents that reason to act

LLM Reasoning 的发展

Language models can generate texts in a simple way predicting the next token auto-regressively.

In 2020 GPT-3 showed us LLMs can solve a variety of NLP tasks by giving them task instructions.

Followup research showed us LLMs can solve question answering tasks by giving them how to bridge the input and output with reasoning.

这个时候的 reasoning 指的是给定上下文，然后从里面挖掘出新的信息来更新 internal context。

LLMs can solve tasks using a few examples.

LLMs can reason to answer questions using Chain-of-Thought Prompting.

但是大模型推理存在问题：lack of knowledge and capabilities。

例子： 有 7 trillion 美元，能买下苹果、英伟达和微软吗？

GPT-4 会回答错误。原因有两个：1. 模型的知识是固定的和有限的。2. 模型不擅长做计算任务。

解决方法有很多，可以用检索来解决知识的有限，可以用 finetune 来解决计算。但是根本问题是模型自训练之初便被设计为文本生成器，而非能与环境交互、主动执行任务的智能体。

如果把环境和任务加到模型的训练里面去，那这个任务很难通用，因为推理时关于 actions, environment 和 tasks 的分布和训练时不一样。

但是人类有很少的知识也能够完成任务，因为人类会推理。

## ReAct

ReAct 是一种结合了 reason 和 act 的 agent。

- Reasoning: update internal belief
- Acting: obtain external feedback
区分 traditional agent 和 language agent

（最大的区别是改变的是 external feedback 和 internal context。）

传统的 Agent： Acting space 完全由环境定义。每一步，会给 Agent context，context 包括外部的反馈以及之前的 agent action。基于 agent context 和最大化 reward 的思想选出下一步 agent action。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251001/fcfeaa4f.png)

Language agent: Acting space 在之前的基础上增加 reasoning 这种类型。reasoning 是一种特殊的 action。reasoning 可以是任何 language sequence，所以它是个无限空间。它没有任何外部的反馈，但是它会改变 agent 内部的上下文。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251001/51309b92.png)

具体如何实现：

只需要在 sample task 写出 what do you think, how you act to solve the task 就行。这个叫做 trajectory。

trajectory 包括 task, thought, action, observation

构建了很多这种 trajectory，甚至可以去 finetune 模型。

Zero-shot ReAct Prompt

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251001/5e3e7c50.png)

作者做了一个对抗性实验，将外部反馈变为空或者给错误的外部反馈（这里通过改变搜索结果），结果发现模型一直可以根据反馈调整 Thought 和 Action。

这里可以看出并不是仅仅是提供外部结果、反馈以及工具的 action 来决定结果，reasoning 在其中起到了制定计划，重新制定计划，跟踪过程的作用。这是一种协同作用。

在前面的 Webshop 上，RL Agent 的成功率是 28.7%，只有 Act 的 Agent 成功率是 30.1%，而 ReAct 成功率是 40%。

把 ReAct 用在 SWE-Bench 上，成功率是 12.7%，相比，LLM 里面最高的成功率是 1.96%，Devin 的成功率是 13.86%。

## Tree of Thoughts

搜索算法已经研究了几十年，为什么过去没把它用到自然语言推理上？

游戏： 24点

Next-token prediction cannot reason deliberately，因为 next-token prediction 是一个线性的机制，是从左到右的进行一个一个的 token 级别的预测。但是对于解决 24 点这个问题来说，需要一直去 backtrack 第一个数是不是合适的。对于 LLM 来说很难 backtrack，很难第一次就生成正确的数字。

Human recognition: Daniel Kahneman Thinking Fast and Slow

两种思考模式：

- System one: Fast and automatic （对应 next token prediction）
- System two: Slow and deliberate （对应 control algorithm）
为什么 Tree Search 没有用来处理模型推理问题呢？因为 space of thinking 空间无限，并且没有反馈，所以不能 enumerate 或者 evaluate。但是传统的搜索是可以做暴力枚举的，象棋游戏也能够写出 evaluate 函数。

但是如果定义一个小的 thinking space，也有一个足够好的外部反馈，那其实是可行的。Tree of Thoughts 用 24 点来做其实是选了一个很好的例子，将问题限制在某一个范围内了。

Tree of Thoughts 的关键思想是语言不仅仅是无限的，它实际上是有 compositional meaning 的，有 semantically coherent units of text。

Tree of thought 关键在于 thought，如果把每一个 token 看成一个 thought，那么它会很容易 generate 但是很难 evaluate。

如果把 whole reasoning 看成一个 thought，它很容易 evaluate，很难 generate。

那么取中间值，把每一个等式作为一个 thought，它相对来说 generate 和 evaluate 都很容易。

所以这里的 thought 就是 a semantically coherent unit text that can be generated and evaluated by LLMs。

那么就可以完成任务了，步骤如下：

1. generate: 用 LLM 一次性写 k 条不同的等式。
1. evaluate: 用 LLM 给每条方程式打分，留下分数高的。
1. 继续循环。
## 总结

- ReAct： reasoning 是 agents 的 internal action （思考与执行互补）
- ToT： reasoning and acting can be similarly planned （统一思考与执行）
# Part 3 Principled framework for language agents

这一部分旨在从上面的经验中跳脱出来，形成一个包罗万象的框架。

- How do we make sense of the various LLM Systems?
- How do we understand them even though they're defining very different tasks and concepts?
因为需要给一个概念性的理解，而不是仅仅从经验出发去解决一个问题。这样才能知道接下来这个领域往哪里走。

## CoALA

CoALA 指 Cognitive Architectures for Language Agents，它包括三个关键概念。

1. Memory: short and long term
1. Action Space: internal and external
1. Decision making: choose an action
这个框架能够让我们快速地比较不同的 agent 论文和方法。因为这三个概念是 agent 的精华。

# Future work

## Train models for agents

Establish model-agent synergy，可以借鉴 GPU 和 deep learning 的发展。

1. 增强 agent 系统层面能做到的事，例如 planning, self-evaluation, calibration。
1. 开源的 agent 基座模型。
1. 规模：训练语料再上一个量级 Next trillion tokens for model training。
## Teach and discover knowledge

不是模仿已有的知识，而是挖掘新知识。

Language agents 有望成为最好的教授，或者是最好的学生，用来反哺人类。

在个性化教育和科学研究方面起到作用。主要涉及到的领域可能为：

- Flexible learning and retrieval (Long-term memory)
- Intrinsic motivation
原因：

1. 现在的 agent 完不成真正的个性化教育，因为缺一个能一直记录、更新、检索学生所有交互的长期记忆系统，而且不能给每个学生都重新训一个模型。
1. 做科研型 agent 也不行，因为科研是开放式任务，没有明确奖励，人类靠好奇心继续探索，agent 缺少这种内在动机机制。


 