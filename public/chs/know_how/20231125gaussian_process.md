---
title: "书籍 Bayesian Optimization Theory and Practice using Python 之Gaussian Process"
date: 2023-11-25T18:01:50+08:00  
tags: ["tech","bayesian"]
format: hugo-md
html-math-method: webtex
thumbnail: https://picsum.photos/id/302/400/250
---

# Gaussian Process

## 1. 理解covariance matrix

Gaussian Process is a stochastic process used to characterize the distribution over function.

GP将一组有限的参数theta从一个连空间拓展到一个连续无限空间的一个无限函数f。

假设我们有两个变量，X1和X2，它俩符合multivariate Gaussian distribution。

![gp_1.png](../../../img/20231125/gp_1.png)

一个高斯分布可以用mean vector 和covariance matrix来表示。均值向量描述了从高斯分布重复采样的集中趋势，协方差矩阵描述了点之间的相关性。（The mean vector describes the central tendency if we were to sample from the Gaussian distribution repeatedly, and the covariance matrix describes how the features of the data are related to each other）

假设mean vector matrix K为：

![\boldsymbol{\mu} = \begin{bmatrix} 
\mu_1 \\\mu_2 \end{bmatrix}](https://latex.codecogs.com/svg.latex?%5Cboldsymbol%7B%5Cmu%7D%20%3D%20%5Cbegin%7Bbmatrix%7D%20%0A%5Cmu_1%20%5C%5C%5Cmu_2%20%5Cend%7Bbmatrix%7D "\boldsymbol{\mu} = \begin{bmatrix} 
\mu_1 \\\mu_2 \end{bmatrix}")

![\boldsymbol{K} = \begin{bmatrix} 
K\_{11}&K\_{12} \\K\_{21}&K\_{22} \end{bmatrix}=\begin{bmatrix} 
\sigma\_{11}^2&\sigma\_{12}^2 \\\sigma\_{21}^2&\sigma\_{22}^2 \end{bmatrix}](https://latex.codecogs.com/svg.latex?%5Cboldsymbol%7BK%7D%20%3D%20%5Cbegin%7Bbmatrix%7D%20%0AK_%7B11%7D%26K_%7B12%7D%20%5C%5CK_%7B21%7D%26K_%7B22%7D%20%5Cend%7Bbmatrix%7D%3D%5Cbegin%7Bbmatrix%7D%20%0A%5Csigma_%7B11%7D%5E2%26%5Csigma_%7B12%7D%5E2%20%5C%5C%5Csigma_%7B21%7D%5E2%26%5Csigma_%7B22%7D%5E2%20%5Cend%7Bbmatrix%7D "\boldsymbol{K} = \begin{bmatrix} 
K_{11}&K_{12} \\K_{21}&K_{22} \end{bmatrix}=\begin{bmatrix} 
\sigma_{11}^2&\sigma_{12}^2 \\\sigma_{21}^2&\sigma_{22}^2 \end{bmatrix}")

K 可以告诉我们，当x1增加的时候，x2变化的大小和方向是如何变化的。K用点积来衡量x1维和x2维的相似性。

![\sigma\_{11}^2 = var(x_1) = E\[(x_1-E\[x_1\])^2\] = E\[(x_1)^2\]](https://latex.codecogs.com/svg.latex?%5Csigma_%7B11%7D%5E2%20%3D%20var%28x_1%29%20%3D%20E%5B%28x_1-E%5Bx_1%5D%29%5E2%5D%20%3D%20E%5B%28x_1%29%5E2%5D "\sigma_{11}^2 = var(x_1) = E[(x_1-E[x_1])^2] = E[(x_1)^2]")

![\sigma\_{12}^2 = \sigma\_{21}^2 = E\[(x_1-E\[x_1\])(x_2-E\[x_2\])\] = E\[x_1x_2\]](https://latex.codecogs.com/svg.latex?%5Csigma_%7B12%7D%5E2%20%3D%20%5Csigma_%7B21%7D%5E2%20%3D%20E%5B%28x_1-E%5Bx_1%5D%29%28x_2-E%5Bx_2%5D%29%5D%20%3D%20E%5Bx_1x_2%5D "\sigma_{12}^2 = \sigma_{21}^2 = E[(x_1-E[x_1])(x_2-E[x_2])] = E[x_1x_2]")

有 E\[x_1\] = E\[x_2\] = 0

图左边和右边的分布为

![\boldsymbol{x\_{left}} = \begin{bmatrix} 
x_1 \\x_2 \end{bmatrix} \sim N(\begin{bmatrix} 
0 \\0 \end{bmatrix} ,\begin{bmatrix} 
1&0 \\0&1 \end{bmatrix})](https://latex.codecogs.com/svg.latex?%5Cboldsymbol%7Bx_%7Bleft%7D%7D%20%3D%20%5Cbegin%7Bbmatrix%7D%20%0Ax_1%20%5C%5Cx_2%20%5Cend%7Bbmatrix%7D%20%5Csim%20N%28%5Cbegin%7Bbmatrix%7D%20%0A0%20%5C%5C0%20%5Cend%7Bbmatrix%7D%20%2C%5Cbegin%7Bbmatrix%7D%20%0A1%260%20%5C%5C0%261%20%5Cend%7Bbmatrix%7D%29 "\boldsymbol{x_{left}} = \begin{bmatrix} 
x_1 \\x_2 \end{bmatrix} \sim N(\begin{bmatrix} 
0 \\0 \end{bmatrix} ,\begin{bmatrix} 
1&0 \\0&1 \end{bmatrix})")

![\boldsymbol{x\_{right}} = \begin{bmatrix} 
x_1 \\x_2 \end{bmatrix} \sim N(\begin{bmatrix} 
0 \\0 \end{bmatrix} ,\begin{bmatrix} 
1&0.6 \\0.6&1 \end{bmatrix})](https://latex.codecogs.com/svg.latex?%5Cboldsymbol%7Bx_%7Bright%7D%7D%20%3D%20%5Cbegin%7Bbmatrix%7D%20%0Ax_1%20%5C%5Cx_2%20%5Cend%7Bbmatrix%7D%20%5Csim%20N%28%5Cbegin%7Bbmatrix%7D%20%0A0%20%5C%5C0%20%5Cend%7Bbmatrix%7D%20%2C%5Cbegin%7Bbmatrix%7D%20%0A1%260.6%20%5C%5C0.6%261%20%5Cend%7Bbmatrix%7D%29 "\boldsymbol{x_{right}} = \begin{bmatrix} 
x_1 \\x_2 \end{bmatrix} \sim N(\begin{bmatrix} 
0 \\0 \end{bmatrix} ,\begin{bmatrix} 
1&0.6 \\0.6&1 \end{bmatrix})")

左侧的协方差项为0，表示变量不相关。右侧的协方差项为0.6，表示存在正相关性。

## 2. 多元高斯分布的边缘分布和条件分布

上述的例子是一个二元高斯分布，它有两个特征，x1和x2。在处理多元高斯分布时，我们通常对特征分布的边缘分布和条件分布感兴趣。

边缘分布

![p(x_1) = N(x_1\|\mu_1, K\_{11})](https://latex.codecogs.com/svg.latex?p%28x_1%29%20%3D%20N%28x_1%7C%5Cmu_1%2C%20K_%7B11%7D%29 "p(x_1) = N(x_1|\mu_1, K_{11})")

![p(x_2) = N(x_2\|\mu_2, K\_{22})](https://latex.codecogs.com/svg.latex?p%28x_2%29%20%3D%20N%28x_2%7C%5Cmu_2%2C%20K_%7B22%7D%29 "p(x_2) = N(x_2|\mu_2, K_{22})")

假设现在观察到x_2的值为a，那这个信息对x_1的分布会有什么影响吗？我们关注的是在x_2=a的条件下x_1的分布，这是个后验概率。

The conditional posterior distribution of x_1 given x_2 = a can be written as:

![p(x_1\|x_2=a) = N(x_1\|\mu\_{1\|2}, K\_{1\|2})](https://latex.codecogs.com/svg.latex?p%28x_1%7Cx_2%3Da%29%20%3D%20N%28x_1%7C%5Cmu_%7B1%7C2%7D%2C%20K_%7B1%7C2%7D%29 "p(x_1|x_2=a) = N(x_1|\mu_{1|2}, K_{1|2})")

The conditional posterior mean and variance are defined as follows:

![\mu\_{1\|2} = \mu_1 + K\_{12}K{22}^{-1}(a- \mu_2)](https://latex.codecogs.com/svg.latex?%5Cmu_%7B1%7C2%7D%20%3D%20%5Cmu_1%20%2B%20K_%7B12%7DK%7B22%7D%5E%7B-1%7D%28a-%20%5Cmu_2%29 "\mu_{1|2} = \mu_1 + K_{12}K{22}^{-1}(a- \mu_2)")

![K\_{1\|2} = K\_{11} - K\_{12}K\_{22}^{-1}K\_{21}](https://latex.codecogs.com/svg.latex?K_%7B1%7C2%7D%20%3D%20K_%7B11%7D%20-%20K_%7B12%7DK_%7B22%7D%5E%7B-1%7DK_%7B21%7D "K_{1|2} = K_{11} - K_{12}K_{22}^{-1}K_{21}")

通过收集data points， 可以不断更新没有观察到的点的后验分布（这里通过x2更新x1），再通过这些分布区预测将来的变化。

## 3. 从高斯分布抽样

如何生成遵循某种特定分布的样本呢？假设我们想要从高斯分布

![N(\mu,\sigma^2)](https://latex.codecogs.com/svg.latex?N%28%5Cmu%2C%5Csigma%5E2%29 "N(\mu,\sigma^2)")

中采样。

一个常见的方法是首先从标准正态分布N(0,1)产生一个随机数x，然后应用scale-location transformation（尺度-位置变化）得到一个样本

![\sigma x + \mu](https://latex.codecogs.com/svg.latex?%5Csigma%20x%20%2B%20%5Cmu "\sigma x + \mu")

。

那么怎么从标准正态分布产生随机数？一般的方法是用标准高斯分布的逆累积分布函数(inverse cumulative distribution function )对均匀随机变量进行变换。例如，如果U均匀分布在\[0,1\]上，那么![\phi^{-1}(U)](https://latex.codecogs.com/svg.latex?%5Cphi%5E%7B-1%7D%28U%29 "\phi^{-1}(U)") 将遵循标准正太分布，其中![\phi^{-1}](https://latex.codecogs.com/svg.latex?%5Cphi%5E%7B-1%7D "\phi^{-1}")是标准正态分布累积函数的倒数。

![gp_2.png](../../../img/20231125/gp_2.png)

总结：从期望的单变量高斯分布中获取随机样本，通过三个步骤：

1.  从均匀分布中采样
2.  使用inverse cumulative function，转换成相应的CDF值
3.  进行scale-location变换

那么，如何拓展到多元情形呢？如何从具有任意均值向量和协方差矩阵的二元高斯分布中采样。
