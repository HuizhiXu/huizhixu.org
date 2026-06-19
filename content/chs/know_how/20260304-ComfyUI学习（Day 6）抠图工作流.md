---
title: "20260304-ComfyUI学习（Day 6）抠图工作流"
date: 2026-03-04T12:11:38.932014
tags: ['tech', 'ai']
description: ""
---

在实际工作中，经常会遇到需要抠图的场景。下面记录了使用 BiRefNet 模型抠图，Segment Anything 抠图，以及结合 Qwen-Image-Edit 2511 编辑模型进行抠图的几种方式。

## **使用 BiRefNet 进行抠图**

BiRefNet 是一个面向高分辨率图像的精细分割模型，主要有以下特点：

- **双边参考机制：结合图像内部与外部的双重参考信息，使模型在锁定目标和刻画细节（特别是边缘区域）时更加稳定和准确。**
- 强大的高分辨率适应能力：可自适应处理从 256×256 到 2304×2304，甚至更大尺寸的图像，在高分辨率下依然保持稳定的分割质量。
- **优秀的细节保留效果：在人像发丝等复杂细节场景中，能够输出非常细腻、自然的抠图结果。**
模型下载地址：git@github.com:viperyl/ComfyUI-BiRefNet.git

这里使用的是 RembgByBiRefNet 节点。Rembg 是一个功能强大的开源去背景工具，大致可以分为三类模型：

- 通用场景模型：如 U2Net、BiRefNet 等；
- 专用场景模型：如针对动漫人物的 ISNet-Anime、针对人像的 U2Net-Human-Seg；
- 交互式模型：如需要辅助点选的 SAM（Segment Anything Model）。
工作流：

![0](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260304/ad463867.png)

从图中可以看到，BiRefNet 在发丝处理上表现非常出色。发丝是抠图中较难处理的部分，因为边缘并非硬边，而是带有一定的半透明过渡。**但是我也在使用的过程中发现有极少数的金边现象。

![1](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260304/6a63fda6.png)

**BiRefNet本质是做前景分割，如果一个图里面人物是主体，花是背景，那么用这个模型可以直接把人分割出来，如果想分割出花，那不太适合。**

下面直接分割出GraceKelly和她的狗狗，如果我想单独分割出狗狗，这个模型是做不到的。

![2](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260304/8d19ac46.png)

## 使用 Segment Anything

**Segment Anything 是一个 基于 prompt 的通用分割模型，可以根据提示词选中并分割图像中的任意目标。**

所以上面例子里面的狗狗，可以用这个模型来实现。

它可以单独分割出某一部分，下面将prompt设定为dog，可以把狗狗单独抠出来。

![3](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260304/0394dd54.png)

**但是它不是精细抠图，用这个模型处理前面的模特图，在毛发等细节上的表现不如BiRefNet细腻，放大后可以看到很多锯齿感。**

![4](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260304/03de33f7.png)

![5](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260304/5381d03f.png)

**这个模型的优点是能按语义/区域逐块抠出不同部分。缺点是推理时间相对较长。**

**如果需要更精细的分割，例如抠背景里面的东西，可以组合使用：先用 Segment Anything 抠出来，然后放大用BiRefNet进行分割**。

## 使用 Qwen-Image-Edit-2511 进行抠图

**还可以换一种思路：现在的编辑模型那么强大，可以用Edit模型的重绘功能来实现抠图效果。这种方法有点算走了弯路。**它无法保证与原图100%的相似性，但是它在解决一些很棘手的问题时效果很好，因为编辑模型的语义理解能力很强。

这里先用Qwen-Image-Edit-2511 编辑模型重绘，然后用RBMG生成透明图。

- 如何查看图像通道数：Show Tensor Shape
- 如何调整通道数：Image Remove Alpha
RMBG本身也是一个抠图模型，也是将前景与背景分离。但是它的效果并不理想。如图，它会把墙和人物一起抠出来。在这里主要用于生成透明图。

![6](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260304/a5f0a10b.png)

在处理头发丝这类复杂边缘时，编辑模型的表现往往非常出色。这个工作流主要缺点是：耗时较长，并且需要自己设定提示词。

![7](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260304/acf00a23.png)

将图中的人物主体抠出来,保持边缘一致，特别是头发丝。

![8](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260304/81967c0f.png)

