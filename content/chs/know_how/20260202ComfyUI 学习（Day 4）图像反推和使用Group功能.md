---
title: "2026-02-02 ComfyUI 学习（Day 4）图像反推和使用Group功能"
date: 2026-02-02T01:38:26.248443
tags: ['tech', 'ai', 'comfyui']
description: ""
---

有时候遇到高质量的图片，希望对其做图像反推，拿到它的 prompt，并基于该 prompt 进行修改或优化。这一过程通常被称为图像打标签或洗图。

## 给图像打标签/洗图

用到的模型有**Qwen3-VL-Instruct** 和**Florence**。

**Qwen3-VL是Qwen系列中最强大的多模态视觉语言模型，Instruct表示它是指令微调版本。**

它的核心能力为：

- **图像理解**：识别名人、动漫角色、产品、地标、动植物等
- **OCR能力**：支持32种语言识别，包括生僻字、古籍字
- **文档解析**：图表、表格、复杂排版文档的精准识别
- **视频理解**：支持2小时以上长视频，帧级精准分析
**这里用的Qwen3-VL-4B-Instruct模型。**

**下载模型:**

在 https://hf-mirror.com/ 搜索QWEN3-VL-INSTRUCT，复制链接，在服务器下载

```plain text
wget https://hf-mirror.com/Qwen/Qwen3-VL-4B-Instruct/resolve/main/model-00002-of-00002.safetensors

```

![1](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260202/1ef2c191.png)

**Florence是微软出的计算机视觉技术的模型。它有1代和2代。**这里用的是Florence-2-base。**Florence-2-base的参数量是0.23B，相对来说小巧一些。**

**图像反推的工作流如下：**

![2](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260202/cdbe9e87.png)

用**Qwen3-VL-Instruct**，图像经过反推之后，得到的提示词为

> **A beautiful Chinese actress with long dark wavy hair, wearing an elegant white gown with a deep V-neckline, puffy sleeves, and a sparkling silver beaded belt.** She is adorned with long dangling diamond earrings and has a soft, natural makeup look with red lipstick. The background is softly blurred, suggesting a glamorous event or red carpet setting. The lighting is bright and flattering, highlighting her delicate features and the luxurious details of her outfit. The overall mood is sophisticated, serene, and elegant.
>

用**Florence**，里面有caption、detailed_caption、more_detailed_caption三种精细度不同的提示词反推功能。用more_detailed_caption得到的提示词为

> **The image is a portrait of a young woman with long dark hair.** She is wearing a white dress with a deep V-neckline and long sleeves. The dress is cinched at the waist with a silver belt. The woman is also wearing large, dangling earrings. She has a serious expression on her face and is looking directly at the camera. The background is blurred, but it appears to be an outdoor setting with buildings and trees visible.
>

注意它里面的text_input需要保持为空，因为Florence的`more_detailed_caption`任务本身不支持外部文本输入，保持`text_input`为空即可。如果不为空，会出现错误：

```plain text
Florence2Run
Text input (prompt) is only supported for 'referring_expression_segmentation', 'caption_to_phrase_grounding', and 'docvqa'

```

比较两段提示词，**可以看出Qwen3-VL-Instruct的prompt反推质量更高，** 具体表现在：

1. 发型上，不仅说"long dark hair"，更精确为"long dark **wavy** hair"（长深色**波浪**发）
1. 服装上，不仅说"white dress"，详细描述为"elegant white **gown** with a deep V-neckline, **puffy sleeves**, and a **sparkling silver beaded belt**"
1. 配饰上，具体到"long dangling **diamond** earrings"（长垂坠**钻石**耳环）
1. 妆容上，详细说明"soft, natural makeup look with **red lipstick**"
1. 它认出这是一位女演员，见识更广。
**但是，Florence有自己的优势。它的描述没有Qwen3-VL-Instruct那么详细和准确，但是速度更快。图中可以看出Florence需要0.106s，Qwen3-VL-Instruct需要0.911s，速度差别很明显。**

选择质量更高还是更快，就看大家的需求了。

### 非常重要的Group功能

下面用一个基于Z-image-Turbo的ControlNet来说明Group功能的重要性以及如何分区。

**通过Group功能对工作流进行分区管理，可以使复杂的节点布局变得清晰有序。**

![3](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260202/b84bd390.png)

例如上面的杂乱的工作流，只要分为预处理阶段，控制网络，生图区域就能井井有条。

![4](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260202/e95513a7.png)

### **预处理区域**

![5](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260202/1a0ee4db.png)

在这一个区域准备好输入，对图像和文本进行预处理。

**对于文本，用Florence进行图像反推，得到文本。
对于图像，用Aux集成预处理器（AIO Aux Preprocessor），用来对参考图片进行预先处理，提取参考的因素，例如深度，姿态和线条等。**

**Reroute** 节点在连线很多的节点很有用，避免修改要重新都连接一遍的痛苦。

### **控制网络区域**

![6](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260202/275761b0.png)

不同模型需要的控制网络不一样，**一般模型用ApplyControlNet，但是 Z-Image-Turbo需要 QwenImageDiffsynthControlnet和ModelPatchLoader**，对应的模型为Z-Image-Turbo-Fun-Controlnet-Union-2.1.safetensors。

要确保将ControlNet模型文件（如`Z-Image-Turbo-Fun-Controlnet-Union-2.1.safetensors`）放置在正确的目录下，例如patch放在models/model_patches里面。

### **生成区域**

![7](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260202/44fe5873.png)

这个区域放生图的过程，里面可以进一步划分子Group，例如模型导入，采样器等等。

**Get Image Size** 的作用是获取图像尺寸，让生成的图和原图尺寸一致。

### **后处理区域**

图片在生成完之后进行放大。

## 图像放大

如果对图像进行精细化处理，需要将得到的图片进行高清放大。

模型方法一般有以下：Upscale Image、Upscale Image By、Upscale Image (using Model) 和 LayerUtility: ImageScaleByAspectRatio V2。

下面是这几个节点。

![8](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260202/3447a89e.png)

其中，Upscale Image **是基于差值的放大，基于原图。如果不知道原图的比例，会有crop和padding。**

Upscale Image By 也是基于差值的放大，是等比例放大，直接选放大倍数。适合快速等比例放大，操作简单。

Upscale Image (using Model) 使用GAN模型进行放大，模型已经设定了放大的倍数，不能再作为参数传进去。适合追求细节真实性的场景，如人脸、纹理。

**LayerUtility: ImageScaleByAspectRatio V2 也是基于差值的放大。可以调的最多， 主要调整两点，比例和采样方式。按宽高比缩放。适合需要精确控制宽高比和采样方式的场景。这一个我使用的最多。**

另外还有一个没写进来，ImageScaleToNormPixels  图像按像素缩放。

