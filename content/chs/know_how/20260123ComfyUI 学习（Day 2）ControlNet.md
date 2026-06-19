---
title: "2026-01-23 ComfyUI 学习（Day 2）ControlNet"
date: 2026-01-23T12:45:29.791477
tags: ['tech', 'ai', 'comfyui']
series: "ComfyUI 学习"
description: ""
---

今天主要学习了Stable Diffusion的一些基本概念，另外动手练习了ControlNet的使用。（因为这是即时的学习笔记，所以难免对有些概念理解不够清晰，如果有错误，恳请指正）

## Stable Diffusion

Stable Diffusion是一种基于扩散过程的文本到图像生成模型。

### 扩散模型的基本思想

- 前向过程：逐渐向一张清晰的图像添加噪声，直到变成完全随机的噪声
- 反向过程：从随机噪声开始，逐步去除噪声，最终生成清晰的图像
- Stable Diffusion学习的是如何从噪声中重建图像
### 模型训练过程

1. 准备数据：拥有大量“图像-文本描述”对（例如，一张小狗的图片和描述“一只棕色的小狗在草地上”）。
1. 前向加噪：随机选取一张训练图片，随机选择一个加噪的步数 `t`，按照这个步数向图片中添加相应程度的高斯噪声，得到一张带噪图片 `x_t`。
1. 模型训练：
- 将 带噪图片 `x_t`、噪声步数 `t` 和 对应的文本描述（经过文本编码器转换）一起输入到U-Net模型中。
- 模型的任务是预测出添加到 `x_t` 中的噪声。
- 计算模型预测的噪声与真实添加噪声之间的损失，并用此损失通过反向传播来更新模型所有参数。
1. 重复迭代：在数百万甚至数十亿的图像-文本对上重复步骤2-3，直到模型收敛。
模型最终学会的是：给定一张噪声图和文本描述，如何预测出正确的噪声并将其移除，从而逐步还原出符合文本描述的清晰图像。

### 模型推理过程

1. 从一张完全随机的纯噪声图片开始。
1. 将这张噪声图和文本“小狗”输入给已经训练好的模型。
1. 模型根据文本提示，预测出当前噪声图中应被移除的噪声。
1. 移除一部分噪声，得到一张稍微清晰一点的图片。
1. 将这张稍微清晰的图作为输入，重复步骤3-4多次（如20-50步），噪声被逐步去除，一张符合“小狗”描述的全新图片就被生成出来了。
## 模型的加载

### 模型如何加载，如何看是三合一加载还是分别加载

如果三个模块合在一起，用一个节点加载，load checkpoint 简易节点。如果三个模块分开，分别加载。

|  | 扩散去噪模块 | VAE | 文本编码模型 | 加载方式 |  |
| --- | --- | --- | --- | --- | --- |
| SD1.5 | SD1.5 | VAE | CLIPL | checkpoint |  |
| SDXL | SDXL | VAE* | CLIP-L + OpenCLIP-G | checkpoint |  |
| FLUX | FLUX（UNet加载器） | VAE**（load VAE节点） | CLIPL+T5（DualClip Loader） | AIO (ALL in one) | 单独发布的FLUX模块，从这个时候起三个模型要单独下载 |
| Qwen image | Qwen image | Qwen vae | Qwen 7b | aio | 如果三个模块合在一起，用一个节点加载，load checkpoint 简易节点。如果三个模块分开，分别加载。 |
| Z Image turbo | Z Image turbo | VAE** (Flux的VAE) | Qwen 4b |  |  |

lightning代表蒸馏的意思，跟turbo类似，所以需要更低的步数，更低的CFG。

Clip 模型常见的模型有t5模型， qwen7b模型，qwen4b模型，最大的区别是是否能识别中文。

Clip L和clip G模型是国外开源的模型。

### 模型都有什么文件类型

| 文件类型 | 例子 | 深度学习框架 |
| --- | --- | --- |
| .ckpt |  | TensorFlow框架 |
| .h5 |  | keras框架 |
| .pt或.pth | 1.5的ControlNet | PyTorch框架 |
| .onnx | 换脸，检测等 | 开放式标准格式 |

## 关于节点的下载

节点就是插件，插件很多时候都是由第三方开发，因此需要自己去github下载和安装。

有部分节点可以在ComfyUI Manager里自动安装。

## ControlNet

ControlNet可以根据输入的条件信息（人物姿势、画面深度），去控制生图的过程。

| 模型名称 | 功能 |
| --- | --- |
| openpose | 控制人物姿势 |
| lineart | 控制线稿和边缘 |
| depth | 控制画面的景深和3D结构 |

其他还有Canny（硬边缘）、MLSD（直线）、Normal（法线图）、Seg（语义分割）等。

### ControlNet的训练过程

1. 准备数据对：
- `(文本提示词， 条件图， 目标图)`。
- 例如：`(“一个男人”, openpose骨架图， 对应姿势的男人照片)`。
1. 创建可训练副本：
- 将原始UNet的 12个编码器模块（负责下采样、提取语义特征）完全复制，形成ControlNet分支。
1. 建立连接：
- 在ControlNet每个编码器模块的输出后，添加一对 “零卷积” 层（权重初始化为零的卷积层）。
- 这些零卷积层的输出，会加到原始UNet对应层级的编码器输出上。
1. 前向传播与损失计算：
- 将条件图输入到ControlNet分支。
- 将文本提示和加噪后的目标图输入到冻结的原始UNet。
- ControlNet分支通过零卷积产生的控制信号，在UNet的每一层“注入”到原始特征中，共同参与去噪预测。
- 计算噪声预测的损失（如L2或Huber损失），只通过ControlNet分支和零卷积进行反向传播，更新它们的参数。原始UNet的参数保持不变。
## ControlNet的使用方式

不同条件类型需要不同的ControlNet（如OpenPose、Depth、Canny等）。

**不同基础模型架构需要不同的ControlNet（如SD1.5用SD1.5的ControlNet，SDXL用SDXL的ControlNet）。**

**ControlNet应用在Condition这条线。它的输入是预处理后的条件图像（如深度图、线稿、姿态图等, 输出连接到ksampler的model。**

### 练习：使用ControlNet在深度、线条和姿态三种控制条件下生成图像。

这是我搭的工作流，用 Grace Kelly的图像来做练习。用的模型是z-image模型，prompt是“正在上课的高中女生”。

![715447b2-427e-492b-8ea9-58fe73c2bd33.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260123/744779cc.png)

### 深度控制

人物的五官轮廓和面部深浅层次与参考图高度一致，甚至发型也是类似的。

![9487ea66-d7d4-4151-9fe0-9eda5bc90b00.jpeg](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260123/a1fdc183.jpeg)

### 线条控制

人物的大致轮廓和面部结构线条与参考图一致。

五官细节有所变化，但保持了短发特征。

![e918b0f8-5f4c-44b3-a2eb-3bcaba0f1045.jpeg](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260123/df65c2ab.jpeg)

### 姿态控制

头部朝向、身体姿态与参考图一致。

发型不再保持短发，可以生成长发等其他样式。

![bf689b22-de09-46e1-99f4-e47b03466cc1.jpeg](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260123/e487f14a.jpeg)

在全身像中，头部姿态细节不够明显，所以用了半身图子再试了一下。

![cba765ca-a1cd-41ce-9b38-29e1d63ebb6c.jpeg](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260123/f21ca012.jpeg)

