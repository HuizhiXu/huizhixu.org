---
author: "Huizhi"
title: "2022-12-10 HuggingFace的Dataset的使用" 
date: 2022-12-10T18:51:00+08:00   
lastmod: 2022-10-30
description: "在数据上吃了很多苦头，数据不符合模型的要求，而造成模型跑不起来，debug的时候走了很多弯路，这样的事情发生了很多次！ 所以特意把HuggingFace里面的数据类都学习一遍。"
tags: ["tech"]
draft: false
pin: false
thumbnail: https://picsum.photos/id/17/400/250
---


[comment]: <> (##  TOC)

[comment]: <> (1. [hub上的数据集]&#40;#datasets from the hub&#41;)

[comment]: <> (   1. [导入数据集]&#40;#import datasets&#41;)



## hub上的数据集<a name="datasets from the hub"></a>

（这里不是互联网上任意的数据集，专指Huggingface的hub上面的，就是可以用关键字直接下载的）

数据集可以在[https://huggingface.co/datasets](https://huggingface.co/datasets) 找到，另外也可以用**`datasets.list_datasets()`
来看有什么数据集，然后通过关键字下载。

```python
from datasets import list_datasets
list_datasets(with_community_datasets = True, with_detaikls = False)
```

很多例子演示的时候，都是直接用hub上的数据集演示，但是我不知道这个数据集里面的构造，尽管照着例子运行成功了，但往往一头雾水。

此时我要看看这个数据集里面到底有啥东西，可以导入dataset builder来看看。（这个例子里面我们导入的数据集是”rotten_tomatoes”）。

```python
!pip install datasets
from datasets import load_dataset_builder
ds_builder = load_dataset_builder("rotten_tomatoes") 

ds_builder.info.description

Movie Review Dataset.
This is a dataset of containing 5,331 positive and 5,331 negative processed
sentences from Rotten Tomatoes movie reviews. This data was first used in Bo
Pang and Lillian Lee, ``Seeing stars: Exploiting class relationships for
sentiment categorization with respect to rating scales.'', Proceedings of the
ACL, 2005.

ds_builder.info.features

{'text': Value(dtype='string', id=None),
 'label': ClassLabel(num_classes=2, names=['neg', 'pos'], id=None)}
```

ds_builder.info.description 告诉我这个数据集的介绍。可以看到这个数据集来自烂番茄这个网站，有5331个正样本，5331个负样本。

ds_builder.info.features  会告诉我数据的特征。它有两个特征， 这里的特征和我们平时说的特征有些许不同。平时说的特征是样本的特征，这里的特征指数据的内容+标签。这两个特征中，一个叫’text’，另一个叫’label’。’label’这个标签有两类——neg和pos。

ClassLabel是什么？做分类任务的时候我们可以用它来构建dataset。

### 导入数据集<a name="import datasets"></a>

接下来可以用load_dataset来导入这个数据集。

如果不写split参数，load_dataset的返回值是一个DatasetDict类。里面只有一个train的数据集。如果写split参数，load_dataset的返回值是一个Dataset类。

```
data = load_dataset('csv', data_files=one_hot_filter_path)

DatasetDict({
    train: Dataset({
        features: ['content', 'labels'],
        num_rows: 1581
    })
})

data = load_dataset('csv', data_files=one_hot_filter_path, split="train")
Dataset({
    features: ['content', 'labels'],
    num_rows: 1581
})
```

这里的split不是切割这个数据集，而是挑选出key为train的数据集。

也可以将split设置为train+test，就挑选出了key 为train和key为test的数据集。

```python
data = load_dataset('csv', data_files=one_hot_filter_path, split="train+test")
Dataset({
    features: ['content', 'labels'],
    num_rows: 3000
})
```

如果数据集在不同的文件，我们想要一起导入。

```python
dataset = load_dataset("csv", data_files=["my_file_1.csv", "my_file_2.csv", "my_file_3.csv"])
```

也可以将文件映射到train和test

```python
base_url = "https://huggingface.co/datasets/lhoestq/demo1/resolve/main/data/"
dataset = load_dataset('csv', data_files={'train': base_url + 'train.csv', 'test': base_url + 'test.csv'})
```

如果选择train数据集的部分数据。

```python
train_10_20_ds =load_dataset('glue', 'mrpc', split='train[10:20]')#选择其中10 行数据
train_10pct_ds = load_dataset('glue', 'mrpc', split='train[:10%]')#选择10%的数据

```

### 划分数据集（Split）

datasets.Dataset.train_test_split(test_size=0.1)

注意不能对DatasetDict运用train_test_split，不然会出现错误' object has no attribute 'train_test_split’，只有对DataDict里面的Dataset运用train_test_split才可以。

```python
data = load_dataset('csv', data_files=one_hot_filter_path)
data
DatasetDict({
    train: Dataset({
        features: ['content', 'labels'],
        num_rows: 1581
    })
})

data=data['train'].train_test_split(test_size=0.1) # 拆分默认shuffle
data

DatasetDict({
    train: Dataset({
        features: ['content', 'labels'],
        num_rows: 1422
    })
    test: Dataset({
        features: ['content', 'labels'],
        num_rows: 159
    })
})
```

### Dataset类

索引

1. Dataset类可以通过下标索引来access某条数据。此时它就像列表一样，可以data[0], data[1], data[-1]。例子如下：

```python

data['train'][0]  # 此时data['train']是Dataset类
{'content': '明日天气雷阵雨转晴，晚上有大雾出现。',
'labels': '天气预报'}

```

1. 可以用’column_name’来得到所有数据。例如我们的数据集中有content和labels两列。我们可以打印出所有的labels。

```python
data['train']['labels']
['天气预报',
 '家政服务',
 '外卖服务',
 '网约车服务',
 '足球资讯',
]
```

也可以打印某一个元素的某列

```python
data['train'][1]['labels']
'家政服务'

data['train']['labels'][1]
'家政服务'
```

### Dataset预处理

这里主要的做法有两步：1.将原始文本切割成字，然后与id对应 ；2.格式化，和机器学习框架适配。

1. tokenize 文本内容

将文本序列切割成一个一个的字(so called token)，然后映射到id。（中文的token主要看预定的规则，在bert-base-chinese里面是字）

我们可以自由选择tokenizer，但通常是和预训练模型用同一个tokenizer。因为不同的模型可能对于特殊token，[SEP],[CLS]的处理是不一样的。例如我们使用了’bert-base-chinese’模型。

这里说一下AUtoTokenizer。什么时候用它呢？就是不知道这个模型是从那个模型里训练出来的，关于bert我们有bertforsequenceclassification，还有很多其他的，不确定的时候就可以用AutoTokenizer

```python

from transformers import AutoTokenizer
from datasets import load_dataset

data = load_dataset('csv', data_files=one_hot_filter_path, split = 'train')
data[0]  # 此时data['train']是Dataset类
{'content': '明日天气雷阵雨转晴，晚上有大雾出现。',
'labels': '天气预报'}

tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")
tokenizer(data[0]['content'])

{'input_ids': [101, 3209, 3189, 1921, 3698, 7440, 7347, 7433, 6760, 3252, 8024, 3241, 
677, 3300, 1920, 7443, 1139, 4385, 511, 102], 
'token_type_ids': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
'attention_mask': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}
```

可以看出来，文本经过tokenize之后，会生成input_ids， token_type_ids和attention_mask。

- input_ids：指文本经过切割之后的字在词典对应的的id。（是的，预训练模型会有一个词典）

形状为(batch_size, sequence_length)。 

如果batch_size为10， sequence_length为256，那么输入的大小为是[10,256]

Bert的输入是`bert:       [CLS] + tokens + [SEP] + padding`

如以上的例子中，input_ids 的结果是

'input_ids': [101, 3209, 3189, 1921, 3698, 7440, 7347, 7433, 6760, 3252, 8024, 3241, 
677, 3300, 1920, 7443, 1139, 4385, 511, 102], 101和102是指CLS和SEP在词表中的id。

- token_type_ids：指token对应的句子id，值为0或1。0表示对应的token属于第一句，1表示属于第二句。  （这里为什么只有两句，因为最多只能接收两个序列。）

```python
from transformers import AutoTokenizer
from datasets import load_dataset

content_1 = '明日天气雷阵雨转晴，晚上有大雾出现。'
content_2 = '后天晴转多云。'
content_3 = '大后天台风降临。'
tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")
tokenizer(content_1,content_2)

{'input_ids': [101, 3209, 3189, 1921, 3698, 7440, 7347, 7433, 6760, 3252,
 8024, 3241, 677, 3300, 1920, 7443, 1139, 4385, 511, 102, 1400, 1921, 3252, 
6760, 1914, 756, 511, 102], 
'token_type_ids': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
0, 0, 1, 1, 1, 1, 1, 1, 1, 1], 
'attention_mask': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 
1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}

tokenizer(content_1,content_2, content_3)
```

tokenizer只能接收两个sequence，如果用这个格式输入两个以上的序列，tokenizer只在前两个sequence作用。

- attention_mask：它指的是这个token应不应该被掩盖起来。如果不应该就是1，应该就是0。如果是0，就不在padding的token上计算attention。

### 输入单序列与输入多序列

注意区分下面两种形式

#### 输入单序列

为什么这两种情况输出的结果不一样呢？

- 两句话在同一个序列

```python
tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english')
model = AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english')
sequence = 'It is cloudy. It is raining.'

inputs = tokenizer(sequence, return_tensors = 'pt')
cls = model(**inputs)

cls_logits = model(**inputs).logits
class_id = cls_logits.argmax().item()
label = model.config.id2label[class_id]
prob = torch.softmax(cls_logits, dim=1).tolist()[0]
print(f'inputs为{inputs}')
print(f'cls的值为：{cls}\ncls_logits的值为：{cls_logits}\nlabel为{label}\nprob为{prob}')
```

输出为

```python
inputs为{'input_ids': tensor([[  101,  2009,  2003, 24706,  1012,  2009,  2003, 24057,  1012,   102]]), 'attention_mask': tensor([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1]])}
cls的值为：SequenceClassifierOutput(loss=None, logits=tensor([[0.1168, 0.0442]], grad_fn=<AddmmBackward0>), hidden_states=None, attentions=None)
cls_logits的值为：tensor([[0.1168, 0.0442]], grad_fn=<AddmmBackward0>)
label为NEGATIVE
prob为[0.5181437730789185, 0.48185625672340393]
```

- 两句话在不同序列

```python
tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english')
model = AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english')
sequence_one = 'It is cloudy.'
sequence_two = 'It is raining.'

inputs = tokenizer(sequence_one, sequence_two, return_tensors = 'pt')
cls = model(**inputs)

cls_logits = model(**inputs).logits
class_id = cls_logits.argmax().item()
label = model.config.id2label[class_id]
prob = torch.softmax(cls_logits, dim=1).tolist()[0]
print(f'inputs为{inputs}')
print(f'cls的值为：{cls}\ncls_logits的值为：{cls_logits}\nlabel为{label}\nprob为{prob}')
```

输出为

```python
inputs为{'input_ids': tensor([[  101,  2009,  2003, 24706,  1012,   102,  2009,  2003, 24057,  1012,
           102]]), 'attention_mask': tensor([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]])}
cls的值为：SequenceClassifierOutput(loss=None, logits=tensor([[ 1.3938, -1.1082]], grad_fn=<AddmmBackward0>), hidden_states=None, attentions=None)
cls_logits的值为：tensor([[ 1.3938, -1.1082]], grad_fn=<AddmmBackward0>)
label为NEGATIVE
prob为[0.924285888671875, 0.07571405917406082]
```

### tokenizer的整个工作过程

那么，tokenizer是如何将原始文本变成 id的呢?

如下面的代码所示，tokenizer.tokenize序列进行切词，tokenizer.convert_tokens_to_ids将token映射到id。

```python
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")

sequence = '明日天气雷阵雨转晴，晚上有大雾出现。'
tokens = tokenizer.tokenize(sequence)
print(tokens) # ['明', '日', '天', '气', '雷', '阵', '雨', '转', '晴', '，', '晚', '上', '有', '大', '雾', '出', '现', '。']

ids = tokenizer.convert_tokens_to_ids(tokens)
print(ids) # [3209, 3189, 1921, 3698, 7440, 7347, 7433, 6760, 3252, 8024, 3241, 677, 3300, 1920, 7443, 1139, 4385, 511]， 与上面的相比， 上面的多了101和102，101和102分别是[CLS]，[SEP]对应的token id。
```

这个过程是可逆的。

```python
tokenizer.convert_ids_to_tokens([3209, 3189, 1921, 3698, 7440, 7347, 7433, 6760, 3
252, 8024, 3241, 677, 3300, 1920, 7443, 1139, 4385, 511])

['明', '日', '天', '气', '雷', '阵', '雨', '转', '晴', '，', '晚', '上', '有', '大', '雾', '出', '现', '。']
```

此外还可以用decode和encode实现这个功能。

tokenizer.encode(sequence)的输入是文本序列，功能是将文本分词后映射到id。

同理tokenizer.decode(tokens_id)的输入是id，输出是文本序列

```python
ids = tokenizer.encode(sequence)

[101, 3209, 3189, 1921, 3698, 7440, 7347, 7433, 6760, 3252, 8024, 3241, 
677, 3300, 1920, 7443, 1139, 4385, 511, 102]

tokenizer.encode_plus(sequence)

{'input_ids': [101, 3209, 3189, 1921, 3698, 7440, 7347, 7433, 6760, 3252,
 8024, 3241, 677, 3300, 1920, 7443, 1139, 4385, 511, 102], 
'token_type_ids': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
'attention_mask': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}

tokenizer.decode([3209, 3189, 1921, 3698, 7440, 7347, 7433, 6760, 3252, 8024, 
3241, 677, 3300, 1920, 7443, 1139, 4385, 511])

'明 日 天 气 雷 阵 雨 转 晴 ， 晚 上 有 大 雾 出 现 。'
```

tokenizer.encode_plus(sequence) 可以替代tokenizer(sequence)

#### 用map来对批量数据进行tokenzie

```python
def tokenization(example):
	return tokenizer(example["content"])

dataset = data.map(tokenization, batched=True)

或者

tokenizer = BertTokenizerFast.from_pretrained("bert-base-chinese")
encoded_data = data.map(lambda e: tokenizer(e['content'], truncation=True, padding='max_length', max_length=512), batched=True)
```

进行Tokenize之后，encoded_data的格式变为

```python
DatasetDict({
    train: Dataset({
        features: ['content', 'labels', 'input_ids', 'token_type_ids', 'attention_mask'],
        num_rows: 1581
    })
})
```

这里的input_ids，token_type_ids和attention_mask是模型的输入，之前的content就不需要了。怎么把content从dataset里面去掉呢？

第二步是格式化，让数据符合模型需要的输入数据格式。

```python
dataset.set_format(type="torch", columns=["input_ids", "token_type_ids", "attention_mask", "labels"])
dataset.format['type']
```

### 如果label是string，怎么变成id？

**align_labels_with_mapping()**

```python
label2id = {"天气预报": 0, "家政服务": 1, "足球资讯": 2}

from datasets import load_dataset

data = load_dataset("csv”, split="train")
data_aligned = data.align_labels_with_mapping(label2id, "label")
```

### 模型输入的数据

input_ids

token_type_ids

attention_mask

position_ids： 表示token在句子中的位置id。

head_mask：1表示head有效，0表示无效

input_embeds：替代input_ids。模型的输入也可以是Embedding后的Tensor， 形状为(batch_size, sequence_length, embedding_dim)

encoder_hidden_states：encoder最后一层输出的隐藏状态序列，模型配置为decoder时使用。形状为(batch_size, sequence_length, hidden_size)

encoder_attention_mask：避免在padding的token上计算attention。

### 模型输出的数据

####  序列经过模型处理之后的数据是什么？

```python
tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english')
model = AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english')
sequence = 'It is sunny.'

inputs = tokenizer(sequence, return_tensors = 'pt')
cls = model(**inputs)
cls # SequenceClassifierOutput(loss=None, logits=tensor([[-4.2761,  4.6390]], grad_fn=<AddmmBackward0>), hidden_states=None, attentions=None)
cls_logits = model(**inputs).logits # tensor([[-4.2761,  4.6390]], grad_fn=<AddmmBackward0>)
```

cls是模型的输出结果，是一个SequenceClassifier类。输出了很多东西，计算结果，loss等。

cls_logits是输出结果的一个属性。

logits可以这样理解：输入数据经过模型处理，进行一大堆计算之后，会出来计算结果。在分类问题上，我们的标签是几类，那么对每类都有一个结果。这个结果，就是logits。

计算出来之后，就要去看数值大的那个对应的下标。然后去id2label的词典里读。model.config.id2label存了id对应的label值。这里为{0: 'NEGATIVE', 1: 'POSITIVE'}

```python
predicted_class_id = cls_logits.argmax().item()

model.config.id2label[predicted_class_id]
```

也可以看计算出来的结果对应的概率。

```python
torch.softmax(cls_logits, dim=1).tolist()[0] # [0]是因为这里是list of list，取第0个元素
```

这两个sequence会合成一句话。所以最后的result只有一个。

logits是什么意思？

在分类中，logits是指分类的分数（下一个步骤就是在SoftMax里面用到）

```python
tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english')
model = AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english')

sequence = 'It is sunny.'
inputs = tokenizer(sequence, return_tensors = 'pt')
labels = torch.tensor([1]).unsqueeze(0)
labels
tensor([[1]])

output = model(**inputs,labels = labels)
output
SequenceClassifierOutput(loss=tensor(0.0001, grad_fn=<NllLossBackward0>), 
logits=tensor([[-4.2761,  4.6390]], grad_fn=<AddmmBackward0>), 
hidden_states=None, attentions=None)

output = model(**inputs)
output

SequenceClassifierOutput(loss=None, logits=tensor([[-4.2761,  4.6390]], 
grad_fn=<AddmmBackward0>), hidden_states=None, attentions=None)
```

output是SequenceClassifierOutput类，它有一个loss，一个logits，一个隐藏状态，一个attentions属性。

如果传入labels，那么就会计算loss。如果传入output_hidden_states = True和 output_attentions= True，那么这两个值也会被计算，否则就是None。

```python
output = model(**inputs, labels = labels, output_hidden_states = True,output_attentions = True)
这个输出太多了，此处不展示
```

每一个输出的属性都可以被拿出来。

```python
output.loss
output.attentions
output.hidden_states
```

也可以用output[:2]取出loss和logits的tuple。

## 参考文献：

 [https://blog.csdn.net/qq_56591814/article/details/120653752](https://blog.csdn.net/qq_56591814/article/details/120653752)