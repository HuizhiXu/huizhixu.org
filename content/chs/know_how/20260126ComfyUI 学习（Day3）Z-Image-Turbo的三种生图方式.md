---
title: "2026-01-26 ComfyUI 学习（Day3）Z-Image-Turbo的三种生图方式"
date: 2026-01-26T12:45:27.575250
tags: ['tech', 'ai']
description: ""
---

## 不同模型的三合一对应关系

|  | Diffusion Model |  | CLIP |  | VAE |  |
| --- | --- | --- | --- | --- | --- | --- |
| Z-image-turbo | z_image_turbo_bf16.safetensors | 12.31GB | qwen_3_4b.safetensors | 8.04 | ae.safetensors | 335.3 |
| Qwen image edit | qwen_image_edit_2511_fp8mixed.safetensors |  | qwen_2.5_vl_7b_fp8_scaled.safetensors |  | qwen_image_vae.safetensors |  |

## Z image turbo

### 1. Z-Image-Turbo 模型介绍

Z-Image-Turbo 是阿里开源的高性能文生图模型。 官网上显示 Z-Image会有三个版本： Z-Image-Turbo， Z-Image-Base和Z-Image-Edit，但是目前只发布了Turbo版本。（https://huggingface.co/Tongyi-MAI/Z-Image-Turbo ）

**核心参数：**

- 模型规模: 6B参数（60亿）
- 推理步数: 仅需8步（NFE），远低于传统模型的20+步
- 硬件要求: 16GB显存即可运行（消费级显卡）
- 推理速度: H100/H800环境下亚秒级生成
- 开源协议: Apache-2.0（可商用）
**优势：**

1. 照片级真实图像生成
1. 精细还原皮肤纹理、发丝、服装材质等细节
1. 双语文本渲染（中英文）
1. 准确渲染复杂中英文文本
1. 提示词增强与推理
1. 内置Prompt Enhancer，具备推理能力
1. 超越表面描述，挖掘潜在世界知识
**技术架构亮点:**

1. S3-DiT架构（Scalable Single-Stream DiT）
1. 将文本、视觉语义token、图像VAE token在序列级别拼接
1. 作为统一输入流，最大化参数效率
1. 相比双流架构更高效
1. 解耦式蒸馏 + 强化学习
1. 将推理流程从20+步缩短到8步
1. 在保持质量的同时大幅提升速度
### 2. Z_Image_Turbo 模型下载

因为服务器不能外网，可以在modelscope/hf-mirror 本地下载模型，也可以复制链接去服务器上下载。前面说过，模型和数据都要按照相应的文件夹名存储。例如这次的模型会在models下面。

![1](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/a00adcbb.png)

除了diffustion_models， clip和vae三部分之外，还有loras。这里的loras 是用来增加图片细节的。

### 3. Z_Image_Turbo 文生图

有一个特别神奇和方便的东西是，有的图片会附带工作流，下面这张图片，直接拖到ComfyUI界面，会出现生成这张图片的工作流。

https://comfyanonymous.github.io/ComfyUI_examples/z_image/

![2](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/5d0e091a.png)

工作流如下

![3](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/671346d7.png)

模型采样算法`AuraFlow`：控制生成图片的不确定性。

空 latent image 相当于在画画时候的建立画布，画布的大小是1024*1024。

VAE解码器：VAE编码先将图片映射到64*64，这样计算的时候参数量不会过于庞大，然后再用VAE解码器释放到1024*1024。

Ksampler的参数：

`cfg`（Classifier-Free Guidance）：提示词引导系数。值越低，图像越自由、越有创意（也越可能忽略提示词）；值越高，对提示词的遵循度越强，但可能牺牲图像质量和多样性。如果模型很厉害，那么cfg调到1就可以了。

`steps`：7步

`sample_name`： euler

`scheduler`: simple

(关于sample_name和Scheduler这两个参数，后面发现用er_sde和beta效果更好。)

`denoise`: 生图模型是一个扩散模型，生成图片属于一个反扩散的过程。它控制从噪声图中开始去噪的步数比例。 `denoise=1.0` 表示从100%的噪声开始（文生图）；`denoise=0.5` 表示从去噪过程的中途开始（即原图添加了适量噪声），因此会保留更多原图信息。

种子数：每一张生成出来的图片都会有一个对应的种子数。随机表示每一张都不一样。

如果想要生成带有工作流信息的照片，可以用这个节点：

![4](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/0a1846ba.png)

### 4. Z_Image_Turbo 图生图+LoRA

下面使用两种LoRA来比较效果。用的prompt是“一个动漫风女孩子”。

1. **用官方自带的LoRA。前面说过，官方的LoRA仅仅用来增加细节。**
![5](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/467b97e7.png)

这里面有一个节点叫做Image Comparer，选rgthree，这个节点可以动态对比原图和参考图。

![6-min](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/95746d03.gif)

这是图生图的任务，所以一定会参考原图，那么会参考多少原图？

- 图像的尺寸信息会被参考
- 图像的已有的元素会被参考。如果要更多参考已有的元素，应该把 denoise 设小一些。因为这张图片对于工作流来说是已经被聚集好的图片，工作流只需要在里面重新添加一些粒子，然后再次降噪，就可以生成一个全新的一张图片。
改变denoise就可以设置参考原图的强度，这是设为0.6的时候。

![7](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/9c7e45a1.JPEG)

1. **下载其他的LoRA**
在liblib下载OVC模型，放置在文件夹models/loras/z_image下面。（**再次强调要按照类别存储模型，这样在工作流里选择模型的时候容易区分。**）

![8](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/f41d4d38.png)

用上面这个LoRA，推荐权重 0.8。

Denoise 设为0.9的效果。

![9](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/2bf22957.jpeg)

denoise设为0.64的效果。

![10](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/b5bca7a6.jpeg)

**这里最重要的参数之一就是denoise。denoise是重绘幅度。**

**可以看出，denoise越高，就越靠近lora模型的效果，越来越偏离参考图片。denoise最高的时候，就和原图没什么关系了，唯一有关系的地方就是尺寸，会采用原图的宽高比和分辨率。**

**denoise越低，就越靠近参考图片。**

| denoise值 | 适用场景 |
| --- | --- |
| 1 | 文生图、完全重绘 |
| 0.7-0.9 | 风格大幅转换 |
| 0.4-0.6 | 图像优化、细节调整 |
| 0.2-0.3 | 轻微修复、微调 |

### 5. Z_Image_Turbo 局部重绘

采用Z_Image_Turbo做局部重绘。

![11](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/aeea17e0.png)

增加一个Set Latent Noise Mask，然后右键点击图片，选择Open in Mask Editor + Image Canvas， 把要重绘的地方都mask掉。

![12](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/68aab6ea.png)

如果遮罩太生硬，可以用遮罩模糊生长结点（Grow Mask With Blur），工作流里面有

这张图是我尝试了好几次之后效果稍微好一点的结果。发现Z-Image-Turbo模型改图能力确实很一般，指令遵循能力不行。

![13](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260126/22417bce.jpeg)(https://uvidumfqwzk.feishu.cn/space/api/box/stream/download/asynccode/?code=M2IyZThiMWJkZjc1MjI2YmQ5NTgzYmE2Mjk2ODRmMjFfN245TnFFVTB6MlBzWE1EYjF3dkZUOFF2WTZTOFZNU1hfVG9rZW46RjgyQmIzSEswb0FMMUh4NzFRNWNJZ203bldoXzE3Njk0MjgyNjE6MTc2OTQzMTg2MV9WNA)

**知道模型的能力边界是很重要的。**Z-Image-Turbo的模型能力边界：生图质量高，快速，是一个Turbo模型，但是不擅长改图。

### 图生图和文生图的区别

观察上面的三种方式，会发现有的时候图像直接用一个 Empty Latent Image 与 KSampler相连，有时候需要用 VAE Encode 节点先处理，再加一个Set Latent Noise Mask，再与 KSampler相连。

这里有一个Latent Space的概念。

**潜空间（Latent Space）**

- Stable Diffusion等扩散模型工作在潜空间而非像素空间
- VAE负责在两个空间之间转换：
- VAE Encode：从像素空间到潜空间
- VAE Decode：从潜空间到像素空间
- Empty Latent Image直接创建潜空间数据
**所以在文生图的任务中，是从零开始生成新图像，Empty Latent Image用来创建一个空白的潜空间。在图生图或者局部重绘任务中，需要基于现有的图像进行修改，所以要用VAE Encode将将像素空间的图像转换为潜空间。而Set Latent Noise Mask则指定哪些区域需要重绘，哪些区域保持不变。**

