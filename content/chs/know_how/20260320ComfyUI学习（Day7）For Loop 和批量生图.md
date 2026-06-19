---
title: "2026-03-20 ComfyUI学习（Day7）For Loop 和批量生图"
date: 2026-03-20T12:45:12.600681
tags: ['tech', 'ai']
description: ""
---

## 简单的批量处理

先看一个简单的批量处理。用上次教程提到的抠图来说，下面的工作流可以实现一次性批量抠图。

![1](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260320/859aa7f7.png)

重点是两个节点：**Load Images From Folder (KJ)** 节点和 **Image Save** 节点。

Load Images From Folder (KJ) 节点内部集成了好几步：读取文件夹、生成图片列表和自动遍历。它很适合处理简单的批量任务。

Load Images From Folder (KJ) 节点：

- 参数 image_load_cap 控制导入的张数，如果是1，就是一张一张导入。如果文件夹有10张照片，这个参数大于等于10会导入全部照片。(上图中的文件夹 /home/data/Sopgia/grace_kelly 有14张，设为100表示全部导入。)
Image Save 节点：

- 参数 output_path 可以设置存储的文件夹名，例如这里 output_path 为 sophia_for_loop，就表示生成的照片在/output/sophia_for_loop文件夹下。也可以设置prefix，delimiter 和补充的位数，另外 extension 可以选择存储的格式，有jpeg、png、webp等等。
**如果需要自动遍历图像批次，对一堆图片进行完全相同的处理（比如全部放大4倍，或全部转为黑白），那么 Load Images From Folder 节点是最佳选择，但是如果涉及到比较复杂的循环，就需要用到For Loop了。**

## For Loop

For Loop 是用来进行循环遍历的节点，在批量处理图片时很有用。它更加灵活，在循环内部可以加入条件判断、数学计算等节点，实现动态的处理流程。

### 一次循环

**For Loop** 有两个节点——**For Loop Start** 节点和 **For Loop End** 节点。它俩的中间就是要循环处理的逻辑。

For Loop Start 节点参数：

- 参数 total 是指循环次数，表示 Group Image Matting 工作流，循环三次。
- 参数 image_load_cap 表示每次导入的张数，每一次处理的张数。如果设为2，每次会有2张照片被处理，但是索引是 0-1、1-2、2-3 这种，会有重复。
- start_index ：开始的索引
如果设置了循环次数，但是发现工作流没有循环的话可以检查 **For Loop End**， 它的 value1需要连接一个其他的节点，可以加一个preview或者Show Any节点。

**应用场景：在生图的时候，对于每个 prompt 想要生成 3 张照片。如果直接将 Empty Latent Image 的 batch_size 设为 3，确实可以生成 3 张。但是会发现这 3 张图特别像，这是因为它们共用一个 seed。如果想生成不同的 3 张，最好是改变 seed。改变 seed 这个过程，就可以用 For Loop。**

![2](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260320/cab0b8ae.png)

这个工作流里面的 **For Loop 用一个数学表达式来随机生成种子，然后传入 KSampler**，来达到效果。可以看出 3 张图确实都不一样。

这里有一个关于 batch_any 节点的说明。**几乎所有的教程都推荐 For Loop 和 batch_any 这个节点一起使用。**在b站上看到了关于 batch_any 节点会爆内存的讨论（见：[【ComfyUI】利用for循环实现图片批量处理](https://www.bilibili.com/video/BV1KXpheEE2F/?spm_id_from=333.337.search-card.all.click&vd_source=38080366348b54b88525a9038e742ef6)）。

> 批量处理过程中占用空间不会被释放，每循环一次就会叠加一次。等到空间满了，有可能循环还没有结束，内存已经不够了，Comfyui程序就会异常退出。
>

batch_any 这个节点 把 For Loop Start 节点的 value_1 和循环结果做一个组合，连到 For Loop End 的 initial_value1。它把每一个循环的结果都加入到这个 batch。 我用的过程中也出现了这个错误：

![3](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260320/48bfff55.png)

后来我测试了不加 batch_any 的情况。

![4](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260320/30c6aef0.png)

不加 batch_any 表示，每加载一张照片，就处理一张照片。前面处理的图片会被后面处理的图片覆盖。这里total设为3，现在显示的是第3张图片。

**但是结果是有存储的，我去看了output/sss_no_batch，里面有三张照片。所以在有存储的情况下我觉得不加 batch_any 也是可以的。**（这里如果有人有更明确的经验，那就更好了，可以一起讨论）

## 实现两层循环嵌套

除了一次生成不同 seed 的图片，还有一种应用场景是**对于某个文件夹的照片依次处理，每一次都需要生成多张照片。**在这种情况下可以用循环嵌套。

从文件夹读照片有一个节点叫 Load Image For Loop，它与 Loop Start 和 Loop End 搭配使用。外循环是从文件夹里依次导入照片，内循环是对每一个照片进行不同seed的生成。例如下面的工作流。

![5](https://raw.githubusercontent.com/HuizhiXu/pictures/master/20260320/dae347cc.png)

### 实现三层循环

这个场景又复杂了一些，**假设要对于某个文件夹的照片依次进行处理，每一次都需要生成多张照片，同时另外有一个 prompt 列表，需要对所有照片依次使用这些 prompt。**

一个方法就是用  [**comfyui-lumi-batcher](https://github.com/bytedance/comfyui-lumi-batcher)** 节点。

上面这个场景，就可以把 prompt 按行写到表格里面，用comfyui_lumi_batcher 运行，再结合前面的两次循环的工作流，就可以实现效果。

comfyui-lumi-batcher 的最大的好处是可以任意设置某个节点的值。那就意味着，除了文本，它还能用来做图片的批量导入。如果不想用Load Image For Loop节点，可以把所有的图片压缩成zip文件上传。

comfyui-batcher-lumi 也支持多参数，例如同时设置上传的images和prompt，但是注意，这里面的多参数是一对一的，一个Image得对应一条prompt，它不会自动做乘法。

