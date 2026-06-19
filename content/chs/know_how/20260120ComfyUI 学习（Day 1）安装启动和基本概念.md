---
title: "2026-01-20 ComfyUI 学习（Day 1）安装启动和基本概念"
date: 2026-01-20T12:45:31.917923
tags: ['tech', 'ai']
description: ""
---

最近打算学一下图生图和文生图，主要是用ComfyUI来生成图片和视频，所以打算记录一下这个学习过程。此次学习的目的是达到能够用ComfyUI完成分割、检测、换装、换头和局部重绘等功能。

这次的学习记录我打算分为理论部分和实践部分，因为我之前没有做图像和视频的模型经验，所以打算在应用过程中，去学一些图像模型的知识，理论部分主要写这些图像模型的原理，实践部分就是记录每天的学习细节和效果。

网络上有很多学习资料，我主要学习b站上的这两个博主的内容：

- [啦啦啦的小黄瓜视频专辑-啦啦啦的小黄瓜视频合集-哔哩哔哩视频](https://space.bilibili.com/219572544/lists?sid=3225210&spm_id_from=333.788.0.0)
- [【2026最新ComfyUI工作流】这可能是B站最简单最详细的ComfyUI使用说明书！0基础小白也能轻松学会！全程干货无废话！附ComfyUI整合包+安装教程_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1tjiuBFEch/?spm_id_from=333.788.videopod.episodes&vd_source=4dc66277adc9e3f1f9f949ecbc840fa4)
第一天主要是ComfyUI的安装与启动。

### 一、ComfyUI的安装与启动

### 1. ComfyUI代码下载

在官方GitHub ：https://github.com/Comfy-Org/ComfyUI 的releases界面找到Souce Code zip，下载，解压缩。不推荐[ComfyUI_windows_portable_nvidia.7z](https://github.com/Comfy-Org/ComfyUI/releases/download/v0.9.2/ComfyUI_windows_portable_nvidia.7z) 等版本，因为Souce Code 是最干净的版本。

如果有新版本出现，在服务器上解压之后直接替换源代码。

### 2. 安装环境

现在基本上都不用conda了，uv快统一江湖了。

```plain text
uv sync
uv pip install -r requirements.txt

```

### 3. 启动

要配置环境，指定显卡，指定端口，指定模型下载的路径和网站（国内用hf-mirror）。

每一个comfyUI服务都要指定一个端口。

```plain text
conda activate /home/data/comfyui_env
export PIP_CACHE_DIR=/home/data/tmp
export HF_HOME=/home/data/hf
export TMPDIR=/home/data/mp
export CUDA_VISIBLE_DEVICES=5
HF_ENDPOINT=https://hf-mirror.com python main.py --port 8198 --listen

```

GUI 界面可以访问：`http://127.0.0.1:8188`

如果在wsl里面启动但是想在Windows浏览器访问GUI的话，可以让服务器监听所有网络接口(--listen 0.0.0.0)。

在wsl里面运行

```plain text
python main.py --listen 0.0.0.0 --port 8188
```

在Windows浏览器中访问

```plain text
http://localhost:8199
```

### 4. 安装ComfyUI Manager

https://github.com/Comfy-Org/ComfyUI-Manager

解压缩之后放到ComfyUI文件夹下面的custom_nodes文件夹里面。

### 5. 下载XSHELL和XFTP 8

如果你的工作流在服务器上，那么一定要下载XFTP和XSHELL这两个工具，因为数据在本地和服务器要来回上传，而这些工具有可视化界面，非常方便。最让我惊讶的功能是，双击，文件就能从本地传到服务器。

![1c7742bd-fd02-40ea-8625-3e8629c3c022.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260120/d8a7dff2.png)

## 二、ComfyUI 界面、工作流介绍

### 1. ComfyUI界面

![comfyui界面.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260120/82075559.png)

这个模版从Templates->Getting Started->1.1 Starter -Text to Image导入。

左边是Assets，Nodes， Models，Workflows，节点组和Templates。

Assets（资产）里面可以浏览输入和输出图片。

Nodes用来查询和导入需要的节点。

Models用来查找模型。

Workflows是这个端口下所有的工作流，他们的格式都是.json。

Nodes Map(节点组)用来把不同的节点锁定成组，里面的小眼睛用来隐藏和显示。如果隐藏，运行的时候就跳过。这一步也可以用ctrl+B来完成，B代表bypass。

Templates用来找模板，这里有很多模板，可以学习，也可以直接使用。

**在ComfyUI-0.8.2 下面的文件夹都分门别类写好了哪个子文件夹存放什么，很清晰。**

input：输入的图像文件夹

output: 输出的图像文件夹

models：下载的模型在models，里面可以建立子文件夹，都可以在工作流中被识别

models/LoRAs：存放LoRA模型，建议建立大的例如qwen、wan之类的子文件夹进行区分

models/ControlNet：存放ControlNet模型，建议同样建立qwen、flux之类的子文件夹进行区分

user/default/workflows：工作流，不区分user，是共享的

### 2. 模型

**按功能分：**

图像，视频，音频

模型系列太多，开源的目前用的是：z-image, qwen-image, qwen-edit, wan系列（都是阿里的）。

去年用的多的是Flux（stable-diffusion分出来的公司做的开源），现在也可能用Flux的某些组件。

闭源主要有jimeng等。

**擅长的任务：**

- z-image, qwen-image（图生图，文生图）
- qwen-editor 编辑模型 （用prompt修改）
- Wan （视频系列）
### 3. 工作流基本概念

文生图和图生图用到的模型主要有Unet， CLIP和VAE。文本主要放在CLIP里面，参考图像放在VAE里面。

![comfyui_workflow.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260120/e5800ee6.png)

工作流包括这几块：

- **模型加载器**，分为两类，一类是三合一加载，也叫checkpoint加载，Unet, CLIP和VAE一起被加载。另一类是单独加载，也就是 Unet, CLIP VAE单独加载。单独加载的原因是模型在更新的时候，有可能只单独更新某个模型，例如Unet模型，这样CLIP和VAE就不需要重新再下载一遍。
- 每个模型都会不同的加载方式，例如阿里的系列的CLIP基本都用用qwen加载
- **文本编码器 CLIP**，后面接CLIP text encoder，用 prompt来控制条件生成
- 有可能要接两个CLIP text encoder，一个是正条件，表明图像里要生成什么。另一个是负条件，表明图像里不要生成什么。
- 有可能只要接一个CLIP text encoder，用来写正条件。负条件用ConditioningZeroOut来表示为空。（上图就是这种方式）
- **K采样器（KSampler）**
- 前面只是导入模型，这里用模型做推理，K采样器是最重要的，相当于推理。
- 关于latent_image
- 文生图
- 需要加空latent：
- 只会影响图像和视频的大小和分辨率
- 图生图
- 编码器 VAE （图生图需要），替代空latent
- 为什么要做多次k采样器？
做一次编辑的能力有限，做第二次采样加噪，精修。第三次第四次基本上是Upscale，提升分辨率。

- **解码器 VAE**
- 解码成图像
**上述四部分是每个工作流都有的模块，另外还有ControlNet和LoRA。**

- **ControlNet（图生图）**：指定一个图像，在此基础上修改。
- 可以分为三类
- **根据姿态图POSE**
- 文生图: 根据姿态图来生成
- 模糊控制
- **基于线稿图来修改，基于边缘 Canny**
- 线稿的力度比姿态要强
- 精确控制
- **基于深度，参考的是深度图，可以恢复空间感**
- **LoRA**：
- 有两种LoRA，一种是功能LoRA，用来提速。例如做视频的时候，加速只要4步，不加速要20步。
- 另一种用来调整风格，例如生成某些角色（林黛玉）的风格。值得注意的是，随着基模能力的提升，很多风格都可以直接用基模来生成了。**但是有一些很难生成的概念，例如双手比心，还是要用LoRA来生成。**
这就是我第一天学习的内容。

