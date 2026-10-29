---
date: '2026-02-14'
description: ''
notion_id: 407a221e-f6ab-8152-a064-c689eb0e8dee
tags:
- tech
- ai
- agent
title: 2026-02-14 令人期待的月之暗面的 Agent Swarm
---

最近比较关注的是月之暗面发布的 K2.5 模型，我不仅看了杨植麟的发布视频，也去 Reddit 浏览了了关于 K2.5 的讨论。（讨论链接在这儿: [https://www.reddit.com/r/LocalLLaMA/comments/1qpewj7/ama_with_kimi_the_opensource_frontier_lab_behind/](<https://www.reddit.com/r/LocalLLaMA/comments/1qpewj7/ama_with_kimi_the_opensource_frontier_lab_behind/>) ）

K2.5 的提升主要在以下几个方面：

1. <strong>前端网页能力</strong>：支持上传图片或者视频做同款内容。模型的视觉能力大幅提升。<strong>我觉得这很厉害，因为我们人类接收到信息中最多的是视觉信息而不是文本信息。</strong>

1. <strong>Coding 能力</strong>: 不仅仅是网页前端，Kimi Code 现在支持 images 和 video作为输入，支持多种编程语言。

1. <strong>办公场景（Office）</strong>：能够生成专业级别的 Word 和 Excel 文档，制作专家级的PPT，完成 PDF 的专业排版。

1. <strong>Agent Swarm（Agent 集群）</strong>：通过多个专家智能体协同处理大批量信息，例如调研一百家公司或阅读一百篇论文。单个任务最多可调用100个智能体，工具调用次数上限达 1500 次。

模型发布本身并不稀奇——每个月都有模型发布（没错，百花齐放，大家都在拼命往前赶）。但这次我对里面的 Agent Swarm 有极大的兴趣。从小红书某个大佬那里争取到了一些 Agent Swarm 的测试额度，因为额度有期限，这几天便抓紧时间使用。

测试 Agent Swarm 最大的难点在于找到合适的场景，因为测试 AI 最难的是结合用户（也就是我）的真实需求，这个需要通过精心设计。

官方说 Agent Swarm 特别适合处理大批量任务。<strong>因为它有多个Agent，我认为它应该也具备深度研究功能，它可能是深度研究 + Office + OK Computer + Coding Agent 四者的结合</strong>，其中 OK Computer 是 Coding Agent 的一个分支，更适合前端或者网页任务。

我为 Agent Swarm 设计了三个任务：一个是导览词的撰写以及网站生成（需要信息收集+撰写+网站搭建+多模态生成），另一个是多轮对话的调研并编写微调代码（目的是与之前的深度研究结果做对比）。这两个任务都顺利完成，第三个任务（论文撰写和投稿）因为额度不足没有再测试了。

<strong>总的来说，Agent Swarm 给我带来了全新的体验。尤其是导游词撰写任务，运行了整整 1 小时 19 分钟。整个过程中我一直盯着屏幕，对其它的处理逻辑非常满意。它的每一步都清晰合理，如果这个任务换做我来做，我也会这样处理。</strong> 这种体验很特别，让人耳目一新。市面上 Multi-Agent 系统不少，但我还从没见过配合这么好这么专业的团队。

这个导游词任务集成了信息收集、联网查询和总结、文章撰写、PDF 生成以及网站开发，基本上考察到了月之暗面出的每一个Agent的特性。<strong>做完这个任务我感觉月之暗面之前分散开发的组件——无论是 Office， OK Computer 还是 Coding Agent，都被集成到这个 Agent Swarm 了，这一点很厉害。更重要的是，这里面涉及到的多模态任务都实现了协同，无论是生图，生成音频还是代码，感觉非常非常流畅。</strong>

月之暗面从 K2 之后就不再只做通用的基模，杨植麟在采访中提到要在预训练中加入 Agent，并解决 Agent 的通用性问题。K2.5 也慢慢在实现这个目标。

而这一次整合的 Office 功能，可能是它希望占领办公室的打工人市场，这跟阶跃的电脑桌面助手是一个目的。<strong>但是表现形式上看，我觉得阶跃助手的上限更高，因为它更定制化——用户可以自行添加技能，实现个性化配置。</strong> 月之暗面所有的功能都要在官网进行，并且打包出售。但不是所有买会员的人都需要 PPT 制作功能，或者是 Coding 功能，做财务的人和做自媒体的人需要的技能是不一样的，官网提供的通用Agent很难满足所有人的需求。

最后，关于视觉能力的提升，我最近在读《维特根斯坦传：论天才之责任》。<strong>维特根斯坦提到 “gezeigt” 与 “gesagt” 是有区别的，这两个词中文可以被翻译为“可被显示的”与“可被言说的”。在我看来，这恰好对应了视觉与语言。大语言模型只能处理被言说的内容——即离散符号、语法规则和显式定义。而语境的感觉或者是那些无法通过文字表达的东西，则只能通过显示来表达。 图像模型弥补了这一点。</strong>（当然，这只是我读完第二章后的个人感悟，纯属瞎说）

下面是我测试的两个任务的详细过程。

## 任务一：写中英导游词+创建音频文件+写成网站+PDF排版

我从 2025 年导游考试官网发布的《文化和旅游部办公厅关于组织实施2025年全国导游资格考试的通知》PDF 文件中，提取了部分省市的景点信息，整理成了一份doc文档。里面包含了 12 个省份，大约 100 多个景点。

<strong>官网聊天框下面选择 K2.5 Agent 集群，进入到熟悉的 OK Computer 界面。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/d419225a.png>)

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/20b1dd6b.png>)

<strong>开始分析任务后，系统将任务拆解为多个步骤，并按照步骤创建不同的专家 Agent。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/ff5ceb85.png>)

<strong>我给的任务是四个，Agent Swarm 创建了4个不同的专家，分别是导游词撰写专家、PDF 生成专家、网站开发专家和音频生成专家。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/0bcc2d29.png>)

<strong>每位专家都有工牌，点击角色说明可以看到对该角色的详细诠释，表明专家执行的是定制化任务，严格遵循我给的指令要求。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/78901ce8.jpeg>)

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/272896e3.jpeg>)

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/38613878.jpeg>)

<strong>任务分配后，启动了 6 个并行任务。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/20be65c0.png>)

<strong>页面左侧的热力图可以查看进度。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/edd0a4bd.png>)

<strong>右侧窗口下可以看到所有并行任务的专家，点击可查看每个专家 Agent 的处理内容。</strong>

<strong>专家状态显示为“正在优化”“正在迭代”“正在处理”“正在改进”“正在提取”等动词，有点像 Claude Code 的那些 -ing 单词，估计是模仿。但 Claude Code 的单词本身无意义，而这些动词是有实际意义的，放在这里略显不合适。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/6790f998.png>)

<strong>任务完成后会弹窗（如“陈野：我的任务已完成”），并生成总结。实际上，上面的 6 个并行任务可能只同时开启了 4 个 Agent，因为后面的专家（德鲁、马洛）是在前四个完成之后才开始工作的。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/037d2164.png>)

<strong>任务完成之后，写了一个总结。总结写得很清晰，所有导览词都写在了 JSON 文件中。</strong>

<strong>完成前 6 个省份后，继续处理剩余省份，重复上述过程。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/4144916b.png>)

<strong>导览词写完后，开始执行 PDF 生成和网站开发任务，这里创建了两个专家 Agent：一个 Agent 做 PDF，另一个专家开发网站。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/6750ef86.png>)

<strong>完成后，使用音频生成专家生成中文和英文音频。</strong>

<strong>系统会判断资源消耗，因为景点太多，只选取了几个代表性景点生成音频。最后，用一个项目整合 Agent 确保所有步骤完成。最后用一个项目整合的 Agent，确保每一步都完成。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/221f8187.png>)

<strong>最后交付的结果：</strong>

1. <strong>导游词：12 个 JSON 文件，涵盖 12 个省份 139 个景点的中英文导游词。</strong>

1. <strong>PDF 文件：一份 PDF，包含封面、中英文标题和完整目录。139 个景点的中英文导游词按拼音排序，大小为 1.3MB。</strong>

1. <strong>网站：一个完整的景点导游网站。</strong>

1. <strong>音频文件：24 个音频文件（每个省中文和英文各一个）</strong>

这里我有个失误：没有限制导览词的字数，导致每个景点生成了 1000–1500 词，其实限制一下会更好。

另外，网站启动之后部分功能失效，需要我做后处理优化。我感觉软件工程有些步骤被漏掉了，可能是测试时并没有全面覆盖。（之前用 OK Computer 也有类似感受。）

## 任务二：收集资料，并且来微调模型。

<strong>我的 prompt 写得很明确：这是一个深度调研并编写代码的任务。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/23e97cf2.png>)

<strong>系统创建了三个专家：技术调研专家，技术总结专家和RL代码开发专家。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/82512a69.png>)

<strong>每个专家都有详细的角色说明。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/0b8ccd4b.gif>)

<strong>调研成果包括论文统计和技术方向分布图表，最终生成了可用的微调代码。</strong>

![配图](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260214/ad06a45b.png>)

我本来还想测试深度调研 + 写代码 + 写论文 + 投稿的任务，但上一个任务花费了太多额度，只能等下次有额度再测试。我试用时每次任务消耗 3 个额度，无论任务量多大。不知道之后他们商业化怎么做，因为 token 消耗实在太多。

另外，官网给了一个CS336 课程翻译的例子。这个例子也不错，可以参考。