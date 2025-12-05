---
title: "2025-06-16 Weaviate使用（四） RAG的两种处理方法"
date: 2025-06-16T12:50:37.525837
tags: ['tech']
description: "Single Prompt 和 Grouped Tasks"
---

执行RAG操作过程中，对检索到的条目有两种处理方法：一种是single_prompt，另一种是grouped_tasks。

grouped_task是对所有检索到的条目做一个整体的处理，例如"write a tweet about these facts"， "what do these movies have in common?"。

single_prompt是对每一个检索到的object应用prompt。例如"translate this into French:{title}"。

## Single prompt

```python
# Single prompt
response = movies.generate.near_vector(
    near_vector=query_vector,
    limit=2,
    single_prompt = "Translate this into French:{title}"
)

for o in response.objects:
    print(o.properties["title"])  # Print the title
    print(o.generated)  # Print the generated text (the title, in French)

```

结果为

```python
I, Robot
The translation of "I, Robot" in French is:
Je, robot.

Looper
The word "Looper" translates to "Loupé" in French.

```

从结果可以看出，找出来两个数据”I, Robot”和”Looper”，并且分别翻译成法语。



## Grouped tasks

```plain text
# #Group tasks
response = movies.generate.near_vector(
    near_vector=query_vector,
    limit=2,
    grouped_task = "What do these movies have in common?"
)

for o in response.objects:
    print(o.properties["title"])  # Print the title
print(response.generated)


```

结果为

```plain text
I, Robot
Looper
These movies, "I, Robot" and "Looper", have several things in common:

1. **Science Fiction theme**: Both movies are set in a futuristic world with advanced technology, such as robots and time travel.

2. **Technology-related themes**: The two movies explore the ethics and consequences of emerging technologies like artificial intelligence (as seen in "I, Robot") and time travel (as seen in "Looper").

3. **Existential questions**: Both films pose existential questions about human nature, free will, and what it means to be alive.

4. **Action and suspense**: While both movies have a strong sci-fi element, they also have action-packed and suspenseful elements, making them thrilling rides for the audience.

5. **Influence from literature or pop culture**: "I, Robot" is based on the book of the same name by Isaac Asimov, while "Looper" was inspired by the 2009 film "Paprika" and draws parallels with Philip K. Dick's time travel stories.

6. **Philosophical undertones**: Both movies explore philosophical concepts like the consequences of playing god with technology (as seen in "I, Robot") and the moral implications of time travel (as seen in "Looper").

These commonalities demonstrate that while the specific plots may differ, both films share a rich thematic landscape and a focus on exploring complex ideas through science fiction narratives.

```



从结果可以看出，同样找出来两个数据”I, Robot”和”Looper”，并且总结了它们的共同点。

 