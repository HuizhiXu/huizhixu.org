---
date: '2026-10-28T13:44:33.854693'
description: ''
notion_id: 407a221e-f6ab-800f-a3d2-e541adbde71e
tags: []
title: '20261026 FLUX 3 Image Klein 使用笔记：提示词扩写、布局控制和局部改图

  '
---

这篇主要写 FLUX 3 Image Klein 在 ComfyUI 里的用法，包括怎么选工作流、怎么扩写提示词，以及怎么用 Bounding Box 控制布局、修改图片里的某个元素。

先记住一点：Bounding Box 是可选的。不接它，也可以直接用提示词出图；需要指定物体的位置、大小，或者圈出要修改的区域时，再把它接进来。

## 一、FLUX 3 和工作流

FLUX 3 是 Black Forest Labs 的模型系列，包含图像、视频等不同方向。这次涉及的主要是图像模型。

FLUX 3 Image 和 Klein 的区别，可以先看这张表：

| 项目 | FLUX 3 Image | FLUX 3 Image Klein |
| --- | --- | --- |
| 定位 | 旗舰图像模型 | 更轻量的图像模型 |
| 使用方式 | 托管 API，权重不可下载 | 开放权重，也提供 API |
| 版本 | 云端模型 | 蒸馏版和 Base 版 |
| 速度与质量 | 更侧重复杂构图和精细控制 | 更快，复杂排版能力略弱 |
| 参考价格 | 1K 约 0.048 美元／张 | 1K 约 0.009 美元／张 |
| 提示词 | 支持详细描述和布局控制 | 需要配合提示词扩写，短提示词的效果比较普通 |
| 许可 | 商业 API | FLUX Kommunity License |

FLUX 3 Image 支持文生图、单图编辑、多图参考、布局控制和局部编辑。比如，修改原图中某个对象的颜色、位置、材质或文字。



官方提供了四个 Klein 工作流，按文生图、改图，以及蒸馏版、标准版来区分。

| 工作流名称 | 用途 | 推荐参数 |
| --- | --- | --- |
| ` image_flux3_klein_distilled_t2i ` | 蒸馏版文生图，适合先练手 | Steps 4–16，CFG 1 |
| ` image_flux3_klein_t2i ` | 标准版文生图 | Steps 约 50，CFG 3.5 |
| ` image_flux3_klein_distilled_image_edit ` | 蒸馏版改图 | Steps 4–16，CFG 1 |
| ` image_flux3_klein_image_edit ` | 标准版改图 | Steps 约 50，CFG 1 |

按这份工作流的要求，先把 ComfyUI 升级到 0.41.2。

## 二、Bounding Box 怎么用

Flux 3 Image Klein的最大特点是像素级确定性修改。在之前的工作流上多加了一个Bounding Box。

Bounding Box 就是在画布上画出的框。每个框对应一个元素，记录它的位置、大小和描述。

在不同任务里，它的用途也不同：

- **文生图**：用框安排构图，决定每个元素放在哪里、占多大。

- **改图**：用框圈出要修改的区域，再用提示词说明具体怎么改。

### 先打开画框界面

画框控件只在 Nodes 2.0 里显示。

![](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/ef657e1c.png>)

（图：ComfyUI 版本与工作流界面）



换到 Nodes 2.0

1. 点击左上角的 ComfyUI 图标。

1. 打开菜单里的 **Nodes 2.0**。

1. 回到 **Create Bounding Boxes** 节点，中间就会出现可以拖框的画布。



![](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/c25b6be3.png>)



（图：Nodes 2.0 的打开方式与画框界面）

### 节点解释

**Create Bounding Boxes**

在画布上拖出框，每个框代表一个元素，比如人物、产品或文字。

` background ` 可以接一张图片作为画框时的底图；不接图片，就是空白画布。画好框后，还需要填写内容：

- 物体选 ` obj `，在 description 里描述它。

- 文字选 ` text `，在文字栏里填写要出现的文字，再用 description 补充外观要求。

**FLUX.3 Layout Prompt**

把框选信息和提示词组合成 FLUX 3 能读取的布局描述。需要在这里说明画面内容，或引用框的标签来描述修改要求。

**Preview as Text**

用来检查最终输出的文字，包括框的名字、坐标和描述。例如：

```text
[{"id": "obj_1", "bbox": [103, 0, 410, 179], "desc": "a small white flower hair clip"}]
```

这里：

- ` id ` 是框的名字。

- ` bbox ` 是框的位置和大小。

- ` desc ` 是框内元素的描述。

看到这段内容，说明框选信息已经输出。接下来还要把它连到出图流程的提示词输入里，模型才能用到。



## 三、改图例子：把粉色发夹换成白色小花发夹

这个例子只修改发夹，脸、头发、画风和背景都保持原样。



![](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/178ba270.png>)

### 第 1 步：接好参考图

把原图接到 Create Bounding Boxes 的 ` background `。

同时，这张图还要接到 **Set Reference Multi Latent**，这样模型才能把它当作参考图读取。

只接 ` background `，图片只是画框时的底图，还没有送进图像模型。

画布尽量与原图保持相同比例。

### 第 2 步：框出发夹

在左上角的粉色发夹周围拖一个框，比发夹稍大一点即可。

类型选择 ` obj `，description 填：

```text
a small white flower hair clip
```

这里写的是修改后希望出现的东西。` color_palette ` 可以不填。

### 第 3 步：写修改指令

在 FLUX.3 Layout Prompt 的 prompt 框里填写：

```text
In <ref_image_0>, replace the pink hair clip <obj_1> with a small white flower hair clip, keep the same face, hair, art style and background.
```

这句话的意思是：

> 在第 1 张参考图中，把框选区域里的粉色发夹换成白色小花发夹，脸、头发、画风和背景保持不变。

` <ref_image_0> ` 指第 1 张参考图，第 2 张是 ` <ref_image_1> `。

` <obj_1> ` 是这个例子中发夹区域的标签，实际使用时要以节点输出的名字为准。

### 第 4 步：检查框的名字

先运行一次，查看 Preview as Text。

如果输出的是 ` "id": "obj_1" `，提示词里的 ` <obj_1> ` 就能对应上。如果输出的是其他名字，例如 ` 01 `，提示词里的标签也要一起改。

框的名字和提示词里的标签必须一致。

组合后的文字大致如下：

```text
In <ref_image_0>, replace the pink hair clip <obj_1> with a small white flower hair clip, keep the same face, hair, art style and background.

[{"id": "obj_1", "bbox": [103, 0, 410, 179], "desc": "a small white flower hair clip"}]
```

### 第 5 步：接入出图流程

把 Preview as Text 输出的 ` STRING `，接到改图流程的 prompt／Positive Prompt 文本输入。

![](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/10d2c876.png>)

（片图：发夹改图的节点连接与结果）





## 四、文生图例子：雨天咖啡馆里的橘猫

用bounding box来控制object和文字应该在的位置。

### 第 1 步：画三个框

这个例子的画布设为 1248×1248，与输出保持一致。官方建议先画背景、再画前景：

| 顺序 | 框的位置 | 类型 | 填写内容 |
| --- | --- | --- | --- |
| 1 | 覆盖整张画布 | ` obj ` | ` a cozy cafe interior by a rainy window, warm yellow lights, raindrops on the glass ` |
| 2 | 中间偏下，约占画面的一半 | ` obj ` | ` an orange tabby cat sitting on the windowsill, looking outside ` |
| 3 | 顶部，横向长条 | ` text ` | 文字栏填 ` RAINY DAY CAFE `；description 填 ` a small wooden hanging sign with white painted letters ` |

这里的三个框分别负责咖啡馆环境、橘猫和顶部招牌。

填完如下

![](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/4fbc7279.png>)

### 第 2 步：写布局提示词

在 Layout Prompt 里填写：

```text
A cozy cafe by a rainy window <obj_1>, an orange tabby cat sitting on the windowsill <obj_2>, and a small wooden hanging sign <obj_3> at the top. Warm cinematic lighting, shallow depth of field.
```

这段示例用 ` <obj_1> `、` <obj_2> `、` <obj_3> ` 指代三个框。运行后，先检查 Preview as Text 里的实际 ID，再把提示词中的标签改成一致的名字，尤其要留意文字框的 ID。

### 第 3 步：连接并运行

把输出的 ` STRING ` 接到 Text to Image 流程的提示词输入，再运行出图。

接下来可以只移动橘猫对应的框，其他内容保持不变，观察构图的变化。

例如，把猫放在右下角，或者放在中部偏下，画面的重心会不同。这也是 Bounding Box 最直观的用处：提示词负责描述猫，框负责指定它的位置和大小。

![](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/018c840b.png>)

（图：橘猫位于右下角的结果）

![](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/1fa79133.png>)

（图片：橘猫位于中部偏下的结果）





## 五、提示词上采样

现在生图/视频模型对提示词的依赖越来越重要。Minimax H3 发布模型的时候还提供了一个提示词skill，将提示词写成更专业的六段式提示词。后来，大家发现了与其教大家怎么写提示词，还不如直接在画布里增加提示词增强的功能。在Flux 3里面，这个叫做“提示词上采样”。



“上采样”原本是图像和信号处理里的词。比如把一张 512 像素的图放大到 1024 像素，需要补出原来没有的细节。DALL·E 3 的论文里就用过 upsample 来描述这种做法，后来 Black Forest Labs 等团队也沿用了这个词。提示词扩写借用了这个说法，只不过处理的对象变成了文字。

例如，输入：

> 一个女孩在咖啡馆。

扩写器会把它写成一段更完整的描述，补充光线、镜头、服装、背景、材质和氛围。短提示词像一张信息量很少的小图，扩写之后，模型能拿到更具体的画面信息。



### Prompt Enhancer 在做什么

工作流里的 Prompt Enhancer 使用 Qwen 3.5 9B，按照 System Prompt 的要求，把用户的短请求扩写成一段英文指令。

过程可以理解为：

**参考图和简短请求 → 提示词扩写器 → 详细英文指令 → FLUX 3 Klein 出图**

![](<https://raw.githubusercontent.com/HuizhiXu/pictures/master/c70a9910.png>)

（图：Prompt Enhancer 节点与 System Prompt）

这里的 System Prompt 是写给扩写器的规则，主要包括：

- 看参考图和用户请求，写出详细的英文指令。

- 只输出指令，不加问候、Markdown、JSON、坐标或 ` <> ` 标签。

- 局部修改用 ` Remove… `、` Change…to… ` 等明确的动作开头。

- 整图转换先说明修改范围；多图合成要交代每张图分别提供什么。

- 只描述实际看得到的内容，不编造图里没有的东西。

- 写清修改后的颜色、大小、材质，以及光照、阴影等连带变化。

- 最后说明哪些内容保持不变，涉及人物时保留人物原有特征。

- 一般控制在 50–150 个英文单词。