---
title: "20260331-ComfyUI学习（Day 8）Qwen-Image 风格LoRA训练"
date: 2026-03-31T12:11:28.447481
tags: ['tech', 'ai']
description: ""
---

随着模型能力的提高，LoRA 的训练没有那么必要，一般来说多花点功夫在提示词上面可以达到同样的效果。

但是后来发现一个绝佳应用场景——**弥补开源和闭源的差距**。如果很喜欢某个闭源模型的某种图片的风格，但是手头上只有开源模型，那么就可以训练 LoRA 来达到同样的效果。

这是两种不同的 LoRA 训练。

如果本地没有资源，可以用 Modelscope 提供的资源免费训练。如果本地有算力，可以在本地训练，这样不需要排队，更有效率。

Mr. Doddle 风格是一种粗线条风格，用即梦直接识别 Mr. Doddle 风格，画出很萌的图，我很喜欢这种风格。

> 一張塗鴉作品，密密麻麻重疊，不同種類小猫塗鴉，色彩鮮明和諧，用 Mr Doodle 風格，畫面全部布滿，沒有留白空隙，大師級作品，大師艺术風格，大胆前卫的大師级作品，抽象概念
>

![image1.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260331/ef224882.png)

同样的 Prompt（「小猫」改成「小狗」），给 Qwen-Image-2512，会产生和上面画风完全不一样的图。

![image2.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260331/06847798.png)

所以就考虑自己训练 LoRA 模型来实现啦！

我选择的框架是 [musubi_tuner](https://github.com/kohya-ss/musubi-tuner)，它可以微调不同的生图模型（qwen-image、z-image、flux 等等），除了 LoRA 模型之外，也可以直接 Finetuning。（另外同事也推荐了 AI-Tookit，操作更简单。）

---

## **Qwen Image 资源**

模型文件见 Hugging Face：

- [Qwen-Image_ComfyUI（Comfy-Org）](https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/tree/main)
### **步骤概览**

### **1.1 模型下载**

从上述仓库下载 **DiT**、**Text Encoders** 和 **VAE**：

|  | DiT | Text Encoders | VAE |
| --- | --- | --- | --- |
| Qwen-Image | `split_files/diffusion_models/qwen_image_2512_bf16.safetensors`（约 40.9GB） | `split_files/text_encoders/qwen_2.5_vl_7b.safetensors`（约 16.6GB） | `split_files/vae/qwen_image_vae.safetensors`（约 254MB） |

### **1.2 准备数据集和配置文件**

**数据集**

我用上面的 prompt 在 jimeng 上生成了 26 张图，基本上都是一些小猫小狗小兔小龙小猪小马。

![image3.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260331/29e908ba.png)

**Caption 文本文件**

把 prompt 写入 caption 文本文件中，与图像同名，扩展名改为 `.txt`。

把数据集和 caption 文件放入 `target_images`。

![image4.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260331/44332108.png)

**配置文件**

对于数据集需要创建一个 TOML 文件，里面指定图片文件夹、缓存文件夹、图片分辨率、`batch_size` 等。`batch_size` 指一个批次用多少张图训练。

```toml
[general]
resolution = [936, 1664]
caption_extension = ".txt"
batch_size = 2
enable_bucket = true

[[datasets]]
image_directory = "/home/data/Sophia/image_lora/resources/20260331/target_images"
cache_directory = "/home/data/Sophia/image_lora/resources/20260331/cache_directory"
num_repeats = 1
```

**目录结构示例**

```plain text
/path/to/target_images/
├── image1.jpg
├── image1.txt           # 对应的 caption
├── image2.jpg
├── image2.txt
└── ...
```

---

## **训练步骤**

Git clone 代码和安装环境就不说了，官方代码仓库都有说明。

在真正训练之前需要做两步 cache 的操作，主要是为了训练效率。

### **1. Text Encoder cache**

```bash
python src/musubi_tuner/qwen_image_cache_text_encoder_outputs.py \
    --dataset_config /home/data/Sophia/image_lora/loras_training/qwen_image/dataset_config.toml \
    --text_encoder /home/data/ComfyUI/models/text_encoders/qwen_2.5_vl_7b.safetensors \
    --batch_size 1 \
    --model_version original
```

**做什么：** 将图片的 caption 通过 Qwen2.5-VL 编码成 embedding 向量，作为 DiT 的输入。

**为什么要做这一步：** 文本编码只依赖 caption，与训练过程无关，可以预先计算并保存。训练时若每一步都现场跑一遍 Qwen2.5-VL，会极慢、占大量显存，且 I/O 与算力都浪费在重复的文本编码上。

### **2. Latent cache**

```bash
python src/musubi_tuner/qwen_image_cache_latents.py \
    --dataset_config /home/data/Sophia/image_lora/loras_training/qwen_image/dataset_config.toml \
    --vae /home/data/ComfyUI/models/vae/qwen_image_vae.safetensors \
    --model_version original
```

**做什么：** 把数据集里的像素图提前用 Qwen-Image 的 VAE 编成 latent。

**为什么要做这一步：** 图片编码只依赖像素，与训练过程无关，可以预先计算并保存。训练 DiT/LoRA 是在 latent 空间做的，训练时若每一步都现场跑一遍 VAE 编码，会让效率变低。

### **3. lora_train**

```bash
CUDA_VISIBLE_DEVICES=6,7 accelerate launch \
  --num_processes 1 --num_cpu_threads_per_process 1 --mixed_precision bf16 \
  qwen_image_train_network.py \
  --dit /home/data/ComfyUI/models/diffusion_models/qwen/qwen_image_2512_bf16.safetensors \
  --vae /home/data/ComfyUI/models/vae/qwen_image_vae.safetensors \
  --text_encoder /home/data/ComfyUI/models/text_encoders/qwen_2.5_vl_7b.safetensors \
  --model_version original \
  --dataset_config /home/data/Sophia/image_lora/loras_training/qwen_image/dataset_config.toml \
  --sdpa \
  --timestep_sampling shift \
  --discrete_flow_shift 2.2 \
  --weighting_scheme none \
  --optimizer_type adamw8bit \
  --learning_rate 5e-5 \
  --gradient_checkpointing \
  --max_data_loader_n_workers 2 \
  --persistent_data_loader_workers \
  --network_module networks.lora_qwen_image \
  --network_dim 16 \
  --max_train_epochs 50 \
  --save_every_n_epochs 10 \
  --seed 42 \
  --output_dir /home/data/Sophia/image_lora/resources/models \
  --output_name doddle_style_v2 \
  --log_with wandb
```

**注意：**

- 使用 bf16 精度，fp8 版本不可用。
- LoRA 训练的效果主要取决于总训练步数。
步数公式：

```plain text
总步数 = (图片数量 × Repeats × Epochs) / Batch Size
```

一般训练 1000–5000 步才能收敛。

推荐先增加 Epochs，让这个值在 50–100 之间。另外如果显存允许的话，可以提高 `batch_size`。

我一开始只训练了 16 个 epoch，训练的结果不太好。

[https://app.notion.com](https://app.notion.com)

---

## **Inference**

```bash
CUDA_VISIBLE_DEVICES=6,7 python src/musubi_tuner/qwen_image_generate_image.py \
  --dit /home/data/ComfyUI/models/diffusion_models/qwen/qwen_image_2512_bf16.safetensors \
  --vae /home/data/ComfyUI/models/vae/qwen_image_vae.safetensors \
  --text_encoder /home/data/ComfyUI/models/text_encoders/qwen_2.5_vl_7b.safetensors \
  --model_version original \
  --prompt "一張塗鴉作品，密密麻麻重疊，不同種類小猴塗鴉，色彩鮮明和諧，用Mr Doodle風格，畫面全部布滿，沒有留白空隙，大師級作品，大師艺术風格，大胆前卫的大師级作品，抽象概念" \
  --negative_prompt " " \
  --image_size 1664 928 \
  --infer_steps 25 \
  --guidance_scale 4.0 \
  --attn_mode sdpa \
  --lora_weight /home/data/Sophia/image_lora/resources/models/doddle_style_v2.safetensors \
  --lora_multiplier 2.0 \
  --save_path /home/data/Sophia/image_lora/resources/output/20260331 \
  --output_type images \
  --seed 42
```

**Image size：**

- 确认两个数都能被 16 整除。
- `image_size` 是**先高再宽**（例如 `1664 928` 表示高 1664、宽 928）。
这是最终效果。现在基本上风格一致了。

![image6.png](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260331/11ba97b2.png)

