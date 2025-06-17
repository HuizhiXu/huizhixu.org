---
title: "Weaviate使用（一） 使用ollama启用大模型和向量模型"
date: 2025-06-12T13:45:42.726594
tags: ['tech']
description: ""
---

## 先决条件

在本地用docker-compose.yml部署Weaviate。因为使用Ollama来启动模型，所以在配置文件中要加上ENABLE_MODULES: 'text2vec-ollama,generative-ollama'

```javascript
---
services:
  weaviate:
    command:
    - --host
    - 0.0.0.0
    - --port
    - '8080'
    - --scheme
    - http
    image: cr.weaviate.io/semitechnologies/weaviate:1.30.6
    ports:
    - 8080:8080
    - 50051:50051
    volumes:
    - weaviate_data:/var/lib/weaviate
    restart: on-failure:0
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      ENABLE_API_BASED_MODULES: 'true'
      ENABLE_MODULES: 'text2vec-ollama,generative-ollama'
      CLUSTER_HOSTNAME: 'node1'
volumes:
  weaviate_data:
...

```

在本地安装启动Weaviate之后，运行

```javascript
import weaviate
client = weaviate.connect_to_local()
print(client.is_ready())

```

True表示这个数据库是可用的。

## 准备数据

下面是jeopardy_tiny.json的例子

```javascript
[
    {
        "Category": "SCIENCE",
        "Question": "This organ removes excess glucose from the blood & stores it as glycogen",
        "Answer": "Liver"
    },
    {
        "Category": "ANIMALS",
        "Question": "It's the only living mammal in the order Proboseidea",
        "Answer": "Elephant"
    },
    {
        "Category": "ANIMALS",
        "Question": "The gavial looks very much like a crocodile except for this bodily feature",
        "Answer": "the nose or snout"
    }
    ]

```

## 创建collection

Ollama启动服务，api_endpoint统一为http://host.docker.internal:11434，模型根据模型名填写。

下面表示创建一个名字为Question的collection，同时配置了向量模型和生成模型。

```javascript

questions = client.collections.create(
    name="Question",
    vectorizer_config=Configure.Vectorizer.text2vec_ollama(
        api_endpoint="<http://host.docker.internal:11434>",
        model="nomic-embed-text",
    ),
    generative_config=Configure.Generative.ollama(
        api_endpoint="<http://host.docker.internal:11434>",
        model ="llama3.2"
    )
)

```

## 导入数据

导入三个文本列answer，question和category

```javascript
import weaviate
import requests, json

client = weaviate.connect_to_local()

resp = requests.get(
     "<https://raw.githubusercontent.com/weaviate-tutorials/quickstart/main/data/jeopardy_tiny.json>"
)

data = json.loads(resp.text)

questions = client.collections.get("Question")

with questions.batch.fixed_size(batch_size=100) as batch:
    for i, d in enumerate(data):
        print(f"importing question: {i+1}")
        batch.add_object({
            "answer": d["Answer"],
            "question": d["Question"],
            "category": d["Category"],
        })
        if batch.number_errors > 10:
            print("Batch import stopped due to excessive errors.")
            break

failed_objects = questions.batch.failed_objects
if failed_objects:
    print("Failed to import the following objects:")
    print(json.dumps(failed_objects, indent=4))

client.close()

```

这一步到底哪一个属性（Property）被向量化了呢？

所有的文本属性都被向量化了。

向量化规则是这样的：

1. 如果没有设置source_properties，text or text[]类型都会被向量化，除非设置skipped。
1. 按照字母顺序对属性进行排列，然后进行拼接。
例如，如果属性有name和age，排序后总是先拼接age再拼接name，这样可以保证结果的唯一性。
1. 如果vectorizePropertyName为true（默认为false），则在每个属性值前面加上属性名称。
例如，如果属性是name="Alice"，经过这一步后会变成name_Alice。
1. 将（已经加上属性名的）属性值用空格连接起来。
例如，如果属性值是name_Alice和age_25，连接后会变成name_Alice age_25。
1. 在生成的字符串前面加上类名（除非vectorizeClassName为false）
例如，如果vectorizeClassName为true，则将类名加到字符串前面，例如class_name_Alice age_25。
1. 将生成的字符串转换为小写。
1. 对字符串进行向量化
## 检索

```javascript
import weaviate
import json

client = weaviate.connect_to_local()

questions = client.collections.get("Question")

response = questions.query.near_text(query="biology", limit=2)

for obj in response.objects:
    print(json.dumps(obj.properties, indent=2))

client.close()

```

near_text的意思是“输入的query是一个是text格式的内容，用向量模型对它进行向量化，与已有的数据计算相似度。”

除near_text之外，还有near_vector，意思是输入的query是一个vector格式的内容。

检索结果为

```javascript
{
  "answer": "DNA",
  "question": "In 1953 Watson & Crick built a model of the molecular structure of this, the gene-carrying substance",
  "category": "SCIENCE"
}
{
  "answer": "Liver",
  "question": "This organ removes excess glucose from the blood & stores it as glycogen",
  "category": "SCIENCE"
}

```

## 检索生成

这一步除了检索之外，还会用前面配置的大模型进行生成。上面是query，这里是generate。这一步其实就是所谓的RAG了。

```javascript
import weaviate

client = weaviate.connect_to_local()

questions = client.collections.get("Question")
print(questions)
response = questions.generate.near_text(
    query="biology",
    limit=2,
    grouped_task="Write a tweet with emojis about these facts.",
)

print(response.generated)

client.close()

```

这里的grouped_task是对所有检索到的条目做一个整体的处理，例如"write a tweet about these facts"， "what do these movies have in common?"。

除grouped task generation之外，还有一种single prompt generation，它是对每一个检索到的object应用prompt。例如"translate this into French:{title}"。

检索生成结果为

```javascript
"In 1953, Watson & Crick constructed a groundbreaking model of DNA 🎯 - the genetic blueprint. And let's not forget the liver ⚖️, vital for regulating our血糖 by storing excess as glycogen! #ScienceFacts #HealthTips"

```

 