---
author: "Huizhi"
title:  "2023-04-27GPU运行LLaMa模型——用HF的方式推理" 
date: 2023-04-27T18:31:50+08:00  
lastmod: 2023-06-30
description: "很简单的运行LLaMa的方法"
tags: ["tech","ai"]
draft: false
isCJKLanguage: true
pin: false
thumbnail: https://picsum.photos/id/30/400/250
---


在GPU上运行中文LLaMa模型，主要是按照 https://github.com/ymcui/Chinese-LLaMA-Alpaca 这个仓库的方法。
中文LLaMa模型和中文Alpaca的区别是：中文LLaMa在英文llama的基础上扩充了中文词表并且使用了中文数据进行二次训练。中文LLaMa只能进行单轮问答。中文Alpaca经过instruct-tuning 生成，可以进行多轮问答。本次实验主要是针对中文LLaMa模型。

# 文档
模型部署和推理有四种方法，我选择的是用HF的inference接口来进行推理。

[](https://github.com/ymcui/Chinese-LLaMA-Alpaca/wiki/%E4%BD%BF%E7%94%A8Transformers%E6%8E%A8%E7%90%86)[https://github.com/ymcui/Chinese-LLaMA-Alpaca/wiki/使用Transformers推理](https://github.com/ymcui/Chinese-LLaMA-Alpaca/wiki/%E4%BD%BF%E7%94%A8Transformers%E6%8E%A8%E7%90%86) 这里详细讲了用scripts/inference_hf.py来启动模型。

原则上非常简单，直接运行下列的脚本，就可以进行推理。

```
CUDA_VISIBLE_DEVICES={device_id} python scripts/inference_hf.py \\
    --base_model path_to_original_llama_hf_dir \\
    --lora_model path_to_chinese_llama_or_alpaca_lora \\
    --with_prompt \\
    --interactive

```

对参数进行解释：

- base_model是Meta发布的原生llama模型
- lora_model是 这个是LoRa生成的模型，可以在网盘下载，也可以用HF的模型调用（例如ziqingyang/chinese-llama-lora-7b）。模型调用比较简单推荐使用。
- with_prompt 是否将输入与prompt模版进行合并。
- interactive 以交互方式启动，以便进行多次单轮问答。

在实验之前，首先要搞清楚一些概念：

1.  LoRa和Alpaca模型是无法单独完成推理的，需要和META的原生LLAMA结合才能运行。
远程LLAMA模型META提供，LoRa和Alpaca模型这个项目提供。

为什么不能用lora模型单独推理，以我浅显的理解，它freeze了原来的模型，单独加了一些层，后续的中文训练都在这些层上做，所以需要进行模型融合。

2. 用huggingface的推理脚本，需要将模型转换成HF支持的格式。（Don’t worry 作者把脚本都写好了）

# 实践

下面用步骤的形式记录一下整个过程。

## 1. 克隆项目

```
git clone git@github.com:ymcui/Chinese-LLaMA-Alpaca.git
cd Chinese-LLaMA-Alpaca

```

## 2. 安装环境

```
pip install -r requirements.txt

```

这一步出现了ERROR: No matching distribution found for peft==0.3.0dev

解决：最后安装了peft==0.2.0

## 3. 下载meta发布的原生的Llama模型

*   可以下载泄露版本，需要用[磁力链下载](magnet:?xt=urn:btih:ZXXDAUWYLRUXXBHUYEMS6Q5CE5WA3LVA&dn=LLaMA）) 。

[泄露地址在这](https://github.com/facebookresearch/llama/pull/73/files/56de950af8a48c7cae221581e2e3e2c342b2ad82)


*   也可以用HuggingFace上的7B模型

```
mkdir -p models/7B/
wget -P models/7B/ <https://huggingface.co/nyanko7/LLaMA-7B/resolve/main/consolidated.00.pth>
wget -P models/7B/ <https://huggingface.co/nyanko7/LLaMA-7B/raw/main/params.json>
wget -P models/7B/ <https://huggingface.co/nyanko7/LLaMA-7B/raw/main/checklist.chk>
wget -P models/ <https://huggingface.co/nyanko7/LLaMA-7B/resolve/main/tokenizer.model>
```

## 4. 将原版的转换成hf格式

下载这些模型后，models文件夹会出现以下文件夹和文件。如果不是这种层级关系，需要换成这种。

```
models
	tokenizer.model
	7B
    consolidated.00.pth
	  params.json
	  checklist.chk
```

这些文件是PyTorch（`.pth`格式的），是不能被HuggingFace-transformers加载的，需要把这些文件转成HuggingFace格式的才行。

这里有两个选择：

一、 如果转换为HF格式之后，后续用llama.cpp进行部署，用这个脚本convert_llama_weights_to_hf 转换成HF再融合再部署。运行

```
python src/transformers/models/llama/convert_llama_weights_to_hf.py \\
    --input_dir models \\
    --model_size 7B \\
    --output_dir models/7B_hf

```

转换后的模型会放在output_dir也就是models/7B_hf下面。转换后的模型会有一个config.json。

如果后续有的步骤出现错误， **does not appear to have a file named config.json. 要记得把这里的解决方法搬过去。**

（来源：

[https://github.com/hpcaitech/ColossalAI/issues/3324](https://github.com/hpcaitech/ColossalAI/issues/3324)

Basically you have to convert your downloaded weights to Hugging Face Transformers format using this`python src/transformers/models/llama/convert_llama_weights_to_hf.py \\ --input_dir /path/to/downloaded/llama/weights --model_size 7B --output_dir /output/path`

Then you would be able to get the config.json.

Source: [](https://huggingface.co/docs/transformers/main/en/model_doc/llama)[https://huggingface.co/docs/transformers/main/en/model_doc/llama](https://huggingface.co/docs/transformers/main/en/model_doc/llama)

）

二、如果转换为HF格式之后，后续用 HuggingFace-transformers 进行推理，可以把直接合并和转换，运行这一个步骤就可以了。

运行
```
CUDA_VISIBLE_DEVICES=1 python scripts/merge_llama_with_chinese_lora_to_hf.py \\
--base_model  /models/7B \\
--lora_model  ziqingyang/chinese-llama-lora-7b \\
--output_dir /home/user/data/xuhuizhi/llama_pj/models/7B_cn

```

如果出现错误，没有config.json文件，需要运行方法一，把转换后的文件里面的config.json拿过来，也就是说方法一和方法二两个步骤都要运行。

##5. 推理

运行：

```
CUDA_VISIBLE_DEVICES=0 python scripts/inference_hf.py \\
--base_model  /home/user/llama_pj/models/7B_cn \\
--lora_model  ziqingyang/chinese-llama-lora-7b \\
--with_prompt \\
--interactive
```

结果

```
Input:苹果是植物吗
Setting `pad_token_id` to `eos_token_id`:2 for open-end generation.
Response:  I don't know if it was plants or animals, but I do remember seeing lots of them on my way to school every morning and coming home from work in the evening。-sarah brown student at university college for four years before she graduated with her bachelor degree in science after taking all required courses such as chemistry physics biology organic chemistry microbiology cellular immunobiology molecular genetic epidemiological theoretic biochemical physiologically based pharmacokinetic modeling statistics data analysis computer programming laboratory experience coursework research projects internships community service volunteer experiencesnetworking career fair job interviewsjob huntingresume writing cover letterspersonal statementwriting sampleessay editingcritiquesmock interviewpreparationMock Interview Mock Job FairMock Networking EventMock Career FairsMock Cover Letter Writing WorkshopsMock Personal Statement EditingWorkshopNetworking EventsMock Professional Development ProgrammeMock Business School Admission Test PreparationsMock GRE/GMAT Prep CourseMockGPA CalculatorMockPersonasMockResearch ProposalsMockPresentationMockPostersMockPPTSlidesMockMockInteractionMockJobOfferMockoffer mock offerMockMockReferencesMockReferenceLettersMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMockMock
```

不知为何回复一直是英文的。

切换到CPU，也不能用中文回答。

```
CUDA_VISIBLE_DEVICES= python scripts/inference_hf.py \\
--base_model  /home/user/llama_pj/models/7B_cn \\
--lora_model  ziqingyang/chinese-llama-lora-7b \\
--with_prompt \\
--interactive
```

试验输出如下

```
Input:索尼最新的耳机
Setting `pad_token_id` to `eos_token_id`:2 for open-end generation.
Response:  I will not buy this product because it doesnot work well and I don't like how much moneyit costs。-end of classroom conversation about what to do next in their lives after graduation.- end of lecture room discussion on whatafter collegegraduates should be doingnext weekendafter they leave school.- endofclassroombalance between students who are leavingschooland thosewho aren’tthe same age but have been out for longer time periodsthank you verymuchfor your help with my English study book, whichis great! thankyouverymuchfortaking care ofmyEnglishstudybookwhichistooexcellenttoo young people aged under 21 years old at present as many other younger peopleshoot down our plan before we can even get started.- end oflecture room discussionaboutwhat to dowhen two or more adults over twenty oneyearsofageare discussed togetherwithin themore than twice per year when older childrenundertwentyoneyearsinnumberbutthemoresimplythanthatmanyothersmore youthanchildrenagedownourplanbeforewecangetstarteduponestartingoutagain.[Endoffeatoryconversatilonwhathappenswhenolderadultswerebornaswellasthedidnorthenumbertheiragesbecomewithintimeperiodfromthenexttwoyearsonheretogetherforeveryoutherthanormalchild.] End offcourse convoerationsion wthing tha happen whevernold adults were born along wit hte ddid nort he rnth er number ther own ages came up again from then until now once upon another timesometimesonce againeachother timetime ago again] End of lectureroomsdiscussionabouticonshowingsome things happened some others did nothing yetsome thingssometimethatearlierthisweeknowhere
```
# 哈希值进行完整性校验
如果实验过程中不确定自己下载的模型是否完整，可以校验哈希值。官方模型的哈希值可以在仓库里找到。

```
cd modles/7B

echo "6efc8dab194ab59e49cd24be5574d85e  consolidated.00.pth" | md5sum --check -           
echo "7596560e011154b90eb51a1b15739763  params.json" | md5sum --check -

```
如果返回True则一致。

