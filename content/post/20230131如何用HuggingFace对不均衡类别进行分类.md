---
title: "20230131如何用HuggingFace对不均衡类别进行分类"  
date: 2023-01-31T19:31:50+08:00  
draft: true  
pin: true  
summary: "如果用Trainer这个API，只要更新compute_loss方法就可以，如果是用pytorch写的训练代码或者用了huggingface accelerate模型，那么要更新自己模型的forward函数。"  
---

# 如何用HuggingFace对不均衡类别进行分类


## 数据均衡

做文本分类时，如果类别数量差别不大，可以用hugging face的Trainer类，训练代码如下：

```python

model = BertForSequenceClassification.from_pretrained("bert-base-chinese", num_labels=len(labels),
                                                      problem_type="multi_label_classification", id2label=id2label,
                                                      label2id=label2id)

tokenizer = BertTokenizerFast.from_pretrained("bert-base-chinese")

def compute_metrics(p):
    preds = p.predictions[0] if isinstance(p.predictions,
                                           tuple) else p.predictions
    result = multi_label_metrics(
        predictions=preds,
        labels=p.label_ids)
    return result

training_args = TrainingArguments(
    output_dir=model_directory, 
    learning_rate=5e-5,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    num_train_epochs=3,
    dataloader_drop_last=True,
    weight_decay=0.01,
    save_steps=50,
    logging_steps=50
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=data["train"],
    eval_dataset=data["train"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

trainer.train()
trainer.evaluate()
```

model_directory 是模型存储路径，data是数据。

## 数据不均衡

如果类别数据不均衡时，例如 class A有1000个数据，class B有100个数据，也可以用上面的训练代码，但是预测B的效果不会很好。

要解决数据不均衡的问题，可以考虑加一个class weight。加class weight的意思是给class B一个更高的权重，让模型预测的时候多考虑一下class B，方向往class B偏离。

官网给了一个例子，需要我们继承Trainer类，自定义一个类，也就是这里的CustomTrainer，重写compute_loss 这个方法。

在训练的时候只要初始化CustomTrainer类就可以了，也就是把trainer = Trainer(…) 改为trainer = CustomTrainer(…) 

```python
from torch import nn
from transformers import Trainer

class CustomTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.get("labels")
        # forward pass
        outputs = model(**inputs)
        logits = outputs.get('logits')
        # compute custom loss
        loss_fct = nn.CrossEntropyLoss(weight=torch.tensor([0.2, 0.3]))
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss

...
...

trainer = CustomTrainer(
    model=model,
    args=training_args,
    train_dataset=encoded_data["train"],
    eval_dataset=encoded_data["train"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

trainer.train()
trainer.evaluate()
```

直接复制可能会出错。 如果出现了如下错误提示，显示loss_fct和loss错误。

```python
ValueError: Expected input batch_size (2) to match target batch_size (20).
```

所以要改loss_fct，去看看源代码是如何计算loss的。[源代码](https://github.com/huggingface/transformers/blob/v4.17.0/src/transformers/models/bert/modeling_bert.py#L1563-L1583) 进行loss的计算是在BertForSequenceClassification的forward方法里面。回归、二分类和多分类都有不同的loss 计算方法。

```python
# 源代码 L1563-L1583
if labels 
is not None:
            if self.config.problem_type is None:
                if self.num_labels == 1:
                    self.config.problem_type = "regression"
                elif self.num_labels > 1 and (labels.dtype == torch.long or labels.dtype == torch.int):
                    self.config.problem_type = "single_label_classification"
                else:
                    self.config.problem_type = "multi_label_classification"

            if self.config.problem_type == "regression":
                loss_fct = MSELoss()
                if self.num_labels == 1:
                    loss = loss_fct(logits.squeeze(), labels.squeeze())
                else:
                    loss = loss_fct(logits, labels)
            elif self.config.problem_type == "single_label_classification":
                loss_fct = CrossEntropyLoss()
                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))
            elif self.config.problem_type == "multi_label_classification":
                loss_fct = BCEWithLogitsLoss()
                loss = loss_fct(logits, labels)
```

所以如果出现batch_size和target_size 不匹配的问题， 要考虑我们解决的问题是二分类还是多分类的问题，多分类用BCE，代码如下

```python
class CustomTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.get("labels")
        # forward pass
        outputs = model(**inputs)
        logits = outputs.get('logits')
        # compute custom loss
        loss_fct = nn.BCEWithLogitsLoss(
            weight=tensor([0.9999, 3.1111,0.9999, 0.9999, 0.9999,2.1333]))
        loss = loss_fct(logits, labels)
        return (loss, outputs) if return_outputs else loss
```

loss_fct 里面的 weight 的计算可以用sklearn.utils.compute_weight这个方法计算。classes是数据的类别，不重复，y是所有数据的label。
```python
class_weights = class_weight.compute_class_weight('balanced', classes=np.array(data.labels.unique()),
                                                  y=np.array(data.labels))
class_weights = torch.tensor(class_weights, dtype=torch.float)
print(class_weights)
```

如果出现这个错误那，就说明模型训练的时候，有可能模型、输入或者loss在本地device，建议在模型和输入后面加.to(device)。
Hugging Face说Trainer类它自己会识别gpu环境，是不需要把模型和数据转到gpu的。那么最有可能就是loss的计算还在本地。

```python

RuntimeError: Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cpu!
```

最后的解决办法是，在计算loss的时候将loss传到device上面去。

```python

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
loss_fct = nn.BCEWithLogitsLoss(
            weight=tensor([0.9529, 0.9529, 1.8027, 0.9394, 0.9529, 0.9529, 0.9529, 0.9667, 0.9529,
                           0.9529])).to(device)
```

总结：如果用Trainer这个API，只要更新compute_loss方法就可以，如果是用pytorch写的训练代码或者用了huggingface accelerate模型，那么要更新自己模型的forward函数。


## 参考

**[How can I use class_weights when training?](https://discuss.huggingface.co/t/how-can-i-use-class-weights-when-training/1067)**

**[What is the loss function used in Trainer from the Transformers library of Hugging Face?](https://stackoverflow.com/questions/71581197/what-is-the-loss-function-used-in-trainer-from-the-transformers-library-of-huggi)**

**[Custom loss function forward vs. custom_loss](https://discuss.huggingface.co/t/custom-loss-function-forward-vs-custom-loss/21526)**
