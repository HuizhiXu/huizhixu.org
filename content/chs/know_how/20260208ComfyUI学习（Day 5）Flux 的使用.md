---
title: "2026-02-08 ComfyUI学习（Day 5）Flux 的使用"
date: 2026-02-08T12:45:21.159394
tags: ['tech', 'ai', 'comfyui']
series: "ComfyUI 学习"
description: ""
---

## Flux.1 介绍

Flux.1 是黑森林实验室在 2024 年推出的图像生成模型。Flux.1 主要有三个版本：

- Flux.1 [pro] - 最强版本，闭源 API
- Flux.1 [dev] - 开发版，非商用，质量接近 pro
- Flux.1 [schnell] - 快速版，可商用，生成速度快
目前已经发布 Flux.2，学习 Flux.1 是为了学习一些处理细节。

## Flux.1 使用

常用模型文件：

|  | **Diffusion Model** |  | **CLIP** |  | **VAE** |  |
| --- | --- | --- | --- | --- | --- | --- |
| **z-image** | **z_image_turbo_bf16.safetensors** | **12.31GB** | **qwen_3_4b.safetensors** | **8.04GB** | **ae.safetensors** | 335.3MB |
| **Qwen image edit** | **qwen_image_edit_2511_fp8mixed.safetensors** |  | **qwen_2.5_vl_7b_fp8_scaled.safetensors** |  | **qwen_image_vae.safetensors** |  |
| **Flux.1** | **Flux1-dev.safetensors** |  | **t5xxl_fp16.safetensors和clip_l.safetensors** | **type选择Flux** | **ae.safetensors** |  |
| **Flux.1 Fill** | **F.1-Fill-fp16_Inpaint&Outpaint_1.0.safetensors** |  | **t5xxl_fp16.safetensors和clip_l.safetensors** |  | **ae.safetensors** |  |

## 文生图

常用模型文件：

基本的工作流节点依然是导入三个模型的导入，CLIP Text Encode (Prompt) 和 KSampler。注意这里用了两个 CLIP 模型：CLIP-L 和 T5-XXL。除此之外多了两个节点 ModelSamplingFlux 和 FluxGuidance。（注意：SD1.5 和 SDXL 需要有正向和反向的 prompt，但是从 Flux 起就不再需要负向的 prompt 了）

![1.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/859aa7f7.png)

ModelSamplingFlux（模型采样配置）用于调整 Flux 模型的采样参数和噪声调度。 ModelSamplingFlux 连在模型侧，连在 Diffusion Model 之后，然后连接 KSampler。

FluxGuidance（引导强度）控制模型对提示词的遵循程度。FluxGuidance 微调图片的细节，值越大，图越锐利和偏风格化，对提示词的遵循也会更好。FluxGuidance 连在正向提示词之后。然后连接 KSampler。

最大的区别是 KSampler 这个区域。古早的版本是由多个节点组成。

![2.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/cab0b8ae.png)

现在一个 KSampler 就可以代替上面整个 Group，并且效果是一致的。所以后续都只会用简化的 KSampler。

![3.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/48bfff55.png)

注意，在 Flux 里面 cfg 固定为 1。cfg 为 1 的时候反向提示词不起作用，所以用 ConditioningZeroOut。

用以下 Prompt 生成福尔摩斯的图像：

> Sherlock Holmes in his Baker Street study, tall lean figure in burgundy dressing gown, sharp aquiline features, piercing grey eyes, holding a magnifying glass, surrounded by chemistry equipment and scattered newspapers, gaslight illumination, Victorian London fog visible through window
**福尔摩斯在他贝克街的书房中，高瘦的身材穿着酒红色晨袍，轮廓分明的鹰钩鼻面容，锐利的灰色眼睛，手持放大镜，周围环绕着化学实验设备和散落的报纸，煤气灯照明，窗外可见维多利亚时代伦敦的雾气**
>

![holmes.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/30c6aef0.png)

## 图生图：Flux Fill

Flux Fill 是专门用于图像修复和扩展的模型，用重绘技术去填充需要修改的区域。Fill 在重绘的时候会在一定基础上参考原图，如果重绘的内容和原图差别不大，直接用 Fill 可以得到不错的效果。如果重绘的内容和原图差别很大，需要进行多次迭代重绘以及更完善的提示来实现。

Flux Fill 有两种，一种是 inpaint，一种是 outpaint。

inpaint 指向内的局部重绘，outpaint 指向外的扩图。

### Inpaint （局部重绘）

![5.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/dae347cc.png)

模型由基础模型换成了 F.1-Fill-fp16_Inpaint&Outpaint_1.0.safetensors。

去掉了 ModelSamplingFlux。

增加了两个节点：

- InpaintModelConditioning 节点：
- 在做图像修复 / 局部重绘时，告诉模型哪些区域需要保留、哪些区域需要重绘
- 结合 mask 使用，只修改遮罩区域，保持其他部分不变
- Differential Diffusion 差异化扩散
- 根据遮罩对不同区域应用不同的去噪强度
- 使过渡更自然，避免明显边界
使用：右击图片，选择 "Open in MaskEditor"，然后涂抹遮罩，这样就生成了 Mask。

这里使用的 prompt 是：

> A silk, transluscent scarf is wrapped around the neck and flutters in the wind.
>

结果如下，左边是原图，右边是加围巾的效果。

![6.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/a5f0a10b.png)

### Outpaint（扩图）

在原图基础上向外延伸——会根据原图内容和提示词，生成画布外的新区域，创造出更大尺寸的完整图像。

![7.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/acf00a23.png)

模型依然由基础模型换成了 F.1-Fill-fp16_Inpaint&Outpaint_1.0.safetensors。

增加了节点 Pad Image for Outpainting、InpaintModelConditioning 和 Differential Diffusion。

- **Pad Image for Outpainting 节点**：拓展图片外的一个区域，并以蒙版的形式传递给采样器。假设数值为：left 400 top 0 right 400 bottom 1600 feathering 24（羽化 24 像素），表示在这张图片的左右各拓展了 400 个像素区域，下面拓展了 1600 个像素。这些区域就是重绘的区域。
- **InpaintModelConditioning 节点**：把 Pad Image for Outpainting 节点的输出连进来，结合 mask 使用，只修改遮罩区域，保持其他部分不变。这里原图需要保留，新增的左右下区域就是蒙版区域，需要重绘。Noise_mask 设为 True。
Outpaint 我认为比较重要的是写 prompt。最好是**描述完整场景，包含原有内容，强调延伸方向的内容，并且保持风格一致。**

使用的Prompt 如下：

```plain text
A woman in a red elegant dress stands in a room corner. Show her full figure and expand the room to include a small window, wooden floor, and elegant decor. Style: cinematic, clean, realistic.
```

结果：左边是原图，右边是扩图效果，由半身像拓展成了全身像。

![8.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/f41d4d38.png)

### Flux Redux

Redux 是 Black Forest Labs 为 Flux.1 模型开发的图像提示适配器，它是一个图像变换工具。Redux 的将参考图像编码为视觉特征。它有两大用处。

一、Redux 最大的用处是风格提取与复制。它不需要用户提供任何文本描述，可以提取出参考图片的特征，生成风格类似的图片。

二、Redux 可以将多个图形的风格融合在一起，生成混合风格。

它需要用到的模型有：

- Flux 主模型（如 Flux1-dev-fp8.safetensors）
- Flux Redux 模型（Flux1-redux-dev.safetensors）
- CLIP vision 模型（sigclip_vision_patch14_384.safetensors）
这会增加以下节点：

Load CLIP Vision 节点用来导入模型，模型选择 sigclip_vision_patch14_384.safetensors。

Load Style Model 节点用来导入 redux 模型，这里选择 Flux1-redux-dev.safetensors。

Apply Style Model 节点用来应用这个节点。注意这里是应用在 conditioning 上面，也就是图像作为条件。

### **单图作为参考，生成风格一致的图片。**

FluxGuidance 控制与原图的相似程度。

![9.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/74c18fe4.png)

工作流中用 Image Concatenate Multi 节点将输入输出拼接到一起。

结果：左边是原图，右边是原图的类似图。

![10.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/e735d747.png)

### **多图作为参考，融合不同图片的风格。**

需要有多个 Apply Style Model 来加载参考图，几张图就加载几个，串联起来一起作为 condition 的输入。

![11.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/aeea17e0.png)

结果：前两张图是参考图，最右是融合图。

![12.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/68aab6ea.png)

注意，上面两个的 prompt 都是 cute anime boy with massive fluffy fennec ears，在上面的两个例子中都是不起作用的。因为这里使用的 ApplyStyleModel 节点无法平衡提示语与提示图片之间的权重关系，如果需要进一步控制，需要安装 AdvancedReFluxControl 节点来控制。

### **Flux Fill+Redux**

前面说过 Fill 和 Redux 的作用，他们其实结合起来效果更好。最经典的例子就是，可以用两者结合来实现换装。

1. Redux 将参考图像编码为视觉特征，使用服装参考图作为 Redux 的输入，确保生成的服装保持原始设计的风格、纹理和细节
1. Fill 实现精确替换 - 通过蒙版精确指定需要替换的服装区域，保持蒙版外的区域不变。
换装这个功能其实是图像编辑的一种。现在图像编辑可以用 Qwen-Image-Eidt 或者 Flux-2-Klein 一步到位。这里还是用 Flux 1 的 Fill 和 Redux 来实现，主要学习图生图的思路。

**步骤:**

1. 准备原始人物图像和目标服装的参考图
1. 在原始图上创建蒙版，标记需要换装的区域 (如裙子等)
1. 将服装参考图输入 Redux 获取风格特征
1. 使用 Fill 功能，结合 Redux 的风格引导，在蒙版区域重绘生成新服装
1. Redux 确保生成的服装与参考图风格一致，Fill 确保只改变指定区域
工作流如下：

![13.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/2d1c64a9.png)

这里用了 ReduxAdvanced 节点，因为原来的 Redux 节点无法控制提示词权重。

- **Downsampling Factor**：最重要的参数，控制 Redux 图像对最终结果的影响程度，通过降低参考图像分辨率来减弱其影响，**值为 1** 完全保留参考图像特征。
- **Downsampling Function**：选择不同的插值方法（area、bicubic、nearest-exact）
- **area**：区域插值，适合缩小图像，边缘平滑
- **bicubic**：双三次插值，质量较高，适合一般场景
- **nearest-exact**：最近邻插值，保留锐利边缘
- **Mode**：控制参考图像的裁剪 / 适配方式（keep aspect ratio、center crop, auto crop with mask）
- **keep aspect ratio**：保持宽高比
- **center crop**：中心裁剪
- **auto crop with mask**：根据遮罩自动裁剪
- **Weight**：
- **作用**：Redux 条件的整体权重系数
- **取值范围**：通常 0.0-1.0
结果：

![change_outfit.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/fb7feab1.png)

这次是换装的初次尝试，Fill 和 Redux 结合在一起换装效果一般，对服装和模特的要求很高，需要用纯色背景，简单款式服装，正面站立姿势，并且服装的长短也要保持一致，否则模型不知道怎么画没有服装的地方，例如下面，短裙就变成了长裙。

![change_outfit2.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260208/a0ea1103.png)

