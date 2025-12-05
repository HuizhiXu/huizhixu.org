---
title: "2025-10-28 MiniMax Agent（M2）有惊喜也有失望"
date: 2025-10-28T13:54:09.184144
tags: ['tech']
description: ""
---

MiniMax发布了M2模型，同时限免了Agent。他们Agent之前的Slogan是“Code is cheap, show me the requirement”，擅长的任务包括代码开发、PPT生成等功能。它据说是“国内最好用的Agent”。





我之前想开会员，但看到最基础的定价一个月39刀，比Codex和Cursor还贵，就放弃了。不过最近MiniMax在M2发布期间限时免费，嘿嘿，所以我又回来用了。


## 总结

MiniMax Agent 确实具备完成任务的能力。模型方面既可以选择免费的轻量版本，也可以选用旗舰模型。它的一个显著优点是，在执行任务前会先进行判断——如果任务本身可以由更简单的模型完成，就无需创建复杂计划或委托给其他代理。

与其他智能体一样，MiniMax 在执行任务时支持实时查看进度，随时调试，也支持下载代码到本地运行，甚至还提供版本回滚功能。

我对整体功能和完成度是比较满意的。

不过，它也有一些令人失望的地方。

对于编码任务，我们为什么不用 Cursor、Codex 或 Trae 这类专门工具呢？在网页上编码和调试非常不便，例如第一个“电子衣橱”任务，反复运行多次，每次都要重新下载代码、安装环境、运行程序，过程相当繁琐。如果能直接在 IDE 中修改，体验会好很多。而在其他任务类型上——比如生成绘本、数据可视化或制作 PPT——这些智能体之间的差距又有多大呢？是否足以让我坚定选择 A 而非 B？目前看来，我并不那么确定，因为它们在表现上似乎相差不大。

MiniMax 有一个比较有意思的功能是 Gallery 中的“remix”，我可以基于他人已有的代码进行修改和呈现。但问题是，有多少人会和我有同样的需求呢？



我做了三个测试。

## 第一个任务：电子衣橱

第一个任务非常难。最近换季了，我想做一个电子衣橱，用来管理穿衣和搭配。市面上的电子衣橱产品都限制上传张数，不好用。所以我想在本地自己做一个纯自用的产品demo。

我写了一份产品文档，然后它开始运行。

这是它的呈现。它的第一步是规划和确认。



![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/59900dc5.jpg)



这里不得不提一个很有用的功能——revert。因为我确认的时候打错了字，小的typo会造成歧义，所以我用这个 restore checkpoint 功能直接回到了“需要确认”这一步，然后输入正确的即可。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/446c18ff.png)



任务完成后，它交付给我一个项目代码包，包含各种详细文档和启动代码说明。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/fccee854.png)

我按照启动代码说明在本地启动，中间没有出现错误。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/ef0707fe.png)



这是代码启动后的界面，看起来还不错。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/695e32e5.png)

我点击“添加物品”和“记录穿搭”，里面是空白的，这些功能还没有实现。

于是我进行了一轮反馈：“添加物品和记录穿搭这两个页面都是空白的，请帮我实现这两页，让我可以真正使用。”然后它开始修复bug。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/85db979f.png)

重新下载它交付的代码，运行起来没有问题。点击“添加物品”，这次页面有内容了。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/74a91da4.png)

我填入了一些信息，发现一个bug导致无法进入下一步，于是进行了第三轮对话，要求修复这个问题。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/29b2808b.png)

它调试时的做法还是很清晰的。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/190c32b2.png)



这里我发现每次下载的文件夹都叫 package.zip，感觉有覆盖的风险。



再次打开，一切顺利，现在功能有了。但添加物品失败，我又去反馈了，第四轮。修复好后，分类又没了。再次反馈，第五轮。这样来来回回多次之后，还是添加不了物品。



## 第二个任务：把《河童》做成绘本

第二个测试是把将杨千嬅《河童》做成绘本的prompt直接给MiniMax。



它先规划步骤，让用户确认。



![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/a8351589.jpg)

在程序运行的过程中，我一张一张查看生成的图片，比较震惊的是发现其中一张与 OK Computer 生成的画面非常相似（这个画面对应的歌词是“令这世界别冻”）。

这是MiniMax Agent生成的：

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/389beee0.png)

这是OK Computer生成的：

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/a489dadc.png)

画面如此相似。看起来它们底层调用的是同一类的模型，或者说，使用相同的prompt调用不同模型也能产生相同的效果。

这时不禁让人思考，这些Agent之间的差异到底在哪里？

它的整体功能没有问题。它没有使用点击按钮，而是采用类似PDF浏览的方式不断向上滑动，切换到下一幕很流畅。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/94a516ab.png)



这个任务是一轮完成的。整体来说，MiniMax的任务完成度要高一些，但是OK Computer的画面更美一些。

## 第三个任务：做PPT

第三个任务是做PPT。我仅上传了一个文档，没有写任何额外提示词，直接让它生成PPT。

这个任务是在第一个任务调试期间同时进行的，说明它可以并行处理多个任务，这一点非常强大。

它为我设计了三种风格供选择，我盲选了 A。如果选择的时候版式有预览就好了。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/8087ee5a.png)

MiniMax Agent 一共生成了20页Slides，几乎囊括了我报告中的所有内容。我感觉效果还是蛮好的。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/baecf3f2.png)

它贴心地提供了“Play Slides”的播放功能，整体效果我觉得不错。

![](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20251028/ef913635.png)







 