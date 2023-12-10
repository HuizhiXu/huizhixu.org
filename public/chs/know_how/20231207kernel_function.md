---
title: "Kernel Function"
date: 2023-12-07T18:01:50+08:00  
tags: ["tech","bayesian"]
format: hugo-md
html-math-method: webtex
thumbnail: https://picsum.photos/id/304/400/250
---

# 核函数 Kernel Function

这篇文章主要解决三个问题：

1.  正态分布的表示
2.  核函数是什么，有什么类型
3.  已知先验知识，如何计算后验分布

# 1. 正态分布的表示

正态分布一般表示为

![f \sim N(0,K)](https://latex.codecogs.com/svg.latex?f%20%5Csim%20N%280%2CK%29 "f \sim N(0,K)")

书上写作

![p(f\|x) = N(f\|0,K)](https://latex.codecogs.com/svg.latex?p%28f%7Cx%29%20%3D%20N%28f%7C0%2CK%29 "p(f|x) = N(f|0,K)")

为啥要多写一个f呢？

是因为这个分布是针对f的分布，或者换句话说这里的随机变量是f，再换句话说的话就是说这个随机变量f遵守一个正态分布。

# 2. 核函数是什么，有什么类型

核函数就是协方差。

核函数![K(x_i, x_j)](https://latex.codecogs.com/svg.latex?K%28x_i%2C%20x_j%29 "K(x_i, x_j)")

-   它计算在输入空间中任意两个点的相似度，可以用欧式距离表示。
-   它度量输入空间中两点xi和xj之间的统计关系。
-   它量化xj的变化和xi的相应变化之间的相关性。

选择不同核函数，表示数据点之间的相关性被用不同方式来衡量。

有几种常见的核：

1.  高斯核 Gaussian kernel

squared exponential kernel

![K\_{ij} = k(x_i,x_j) = e^{-\|\|X_i-X_j\|\|^2}](https://latex.codecogs.com/svg.latex?K_%7Bij%7D%20%3D%20k%28x_i%2Cx_j%29%20%3D%20e%5E%7B-%7C%7CX_i-X_j%7C%7C%5E2%7D "K_{ij} = k(x_i,x_j) = e^{-||X_i-X_j||^2}")

这里把负平方距离的指数作为距离度量。当x_i和x_j距离非常远，我们有x_i-x_j 趋向于无穷大，此时k\_{ij}趋向于0。当x_i和x_j相等，k\_{ij}等于1。K是一个介于0和1之间的数，由此就可以表现点之间的相关性。

可调节参数的高斯核，又被叫做isotropic squared exponential kernel

![K\_{ij} = k(x_i,x_j) = \sigma_f^2e^{-\frac{1}{2l^2}\|\|X_i-X_j\|\|^2}](https://latex.codecogs.com/svg.latex?K_%7Bij%7D%20%3D%20k%28x_i%2Cx_j%29%20%3D%20%5Csigma_f%5E2e%5E%7B-%5Cfrac%7B1%7D%7B2l%5E2%7D%7C%7CX_i-X_j%7C%7C%5E2%7D "K_{ij} = k(x_i,x_j) = \sigma_f^2e^{-\frac{1}{2l^2}||X_i-X_j||^2}")

1.  略(以后补充，暂时不是重点)

# 3. 已知先验知识，如何计算后验分布

假设我们有三个无噪声观测值，![D = \\(x_1,f(x_1)), (x_2, f(x_2)),(x_3, f(x_3))\\](https://latex.codecogs.com/svg.latex?D%20%3D%20%5C%7B%28x_1%2Cf%28x_1%29%29%2C%20%28x_2%2C%20f%28x_2%29%29%2C%28x_3%2C%20f%28x_3%29%29%5C%7D "D = \{(x_1,f(x_1)), (x_2, f(x_2)),(x_3, f(x_3))\}")。我们需要对这三个随机变量进行建模。假设mean vector 为![\mu](https://latex.codecogs.com/svg.latex?%5Cmu "\mu")， covariance matrix为![K](https://latex.codecogs.com/svg.latex?K "K")。

这三个变量遵循多元变量的高斯分布

![\bold f = \begin{bmatrix} 
f(x_1) \\f(x_2) \\f(x_3)  \end{bmatrix} \sim N(\mu, K) =N(\begin{bmatrix} 
0 \\0 \\0\end{bmatrix} ,\begin{bmatrix} 
k\_{11}&k\_{12}&k\_{13} \\k\_{21}&k\_{22}&k\_{23}\\k\_{31}&k\_{32}&k\_{33}\end{bmatrix})](https://latex.codecogs.com/svg.latex?%5Cbold%20f%20%3D%20%5Cbegin%7Bbmatrix%7D%20%0Af%28x_1%29%20%5C%5Cf%28x_2%29%20%5C%5Cf%28x_3%29%20%20%5Cend%7Bbmatrix%7D%20%5Csim%20N%28%5Cmu%2C%20K%29%20%3DN%28%5Cbegin%7Bbmatrix%7D%20%0A0%20%5C%5C0%20%5C%5C0%5Cend%7Bbmatrix%7D%20%2C%5Cbegin%7Bbmatrix%7D%20%0Ak_%7B11%7D%26k_%7B12%7D%26k_%7B13%7D%20%5C%5Ck_%7B21%7D%26k_%7B22%7D%26k_%7B23%7D%5C%5Ck_%7B31%7D%26k_%7B32%7D%26k_%7B33%7D%5Cend%7Bbmatrix%7D%29 "\bold f = \begin{bmatrix} 
f(x_1) \\f(x_2) \\f(x_3)  \end{bmatrix} \sim N(\mu, K) =N(\begin{bmatrix} 
0 \\0 \\0\end{bmatrix} ,\begin{bmatrix} 
k_{11}&k_{12}&k_{13} \\k_{21}&k_{22}&k_{23}\\k_{31}&k_{32}&k_{33}\end{bmatrix})")

基于这个数据集D，假设我们现在想知道另一个变量x_4（它对应的f值用f\_\*(x_4)表示）在其他位置的均值和方差的的分布。

问题：f 和f\* 是同一个分布吗？ 不是，用不同的字母表示不同的分布。

f和f\*的分布为

![\bold f \sim N(0,K)](https://latex.codecogs.com/svg.latex?%5Cbold%20f%20%5Csim%20N%280%2CK%29 "\bold f \sim N(0,K)")

![\bold f\_\* \sim N(0,k(x_4,x_4))](https://latex.codecogs.com/svg.latex?%5Cbold%20f_%2A%20%5Csim%20N%280%2Ck%28x_4%2Cx_4%29%29 "\bold f_* \sim N(0,k(x_4,x_4))")

已知先验知识：![p(f\_\*(x_4)\|x_4) = N(f\_\*(x_4)\|0, k(x_4,x_4))](https://latex.codecogs.com/svg.latex?p%28f_%2A%28x_4%29%7Cx_4%29%20%3D%20N%28f_%2A%28x_4%29%7C0%2C%20k%28x_4%2Cx_4%29%29 "p(f_*(x_4)|x_4) = N(f_*(x_4)|0, k(x_4,x_4))") 和![p(f\|x) = N(f\|0,K)](https://latex.codecogs.com/svg.latex?p%28f%7Cx%29%20%3D%20N%28f%7C0%2CK%29 "p(f|x) = N(f|0,K)") ，求后验概率![p(f\_\*(x_4)\|x_4,x,f)](https://latex.codecogs.com/svg.latex?p%28f_%2A%28x_4%29%7Cx_4%2Cx%2Cf%29 "p(f_*(x_4)|x_4,x,f)")。

如何求这个后验概率呢？

我们可以将观察到的数据集与新变量一起构造一个联合分布。

我们已经知道，数据集D最的观测值f和f(x_4)分别遵循分布

![\bold f \sim N(0,K)](https://latex.codecogs.com/svg.latex?%5Cbold%20f%20%5Csim%20N%280%2CK%29 "\bold f \sim N(0,K)")

![f(x_4) \sim N(0, k(x_4,x_4)) = N(0,1)](https://latex.codecogs.com/svg.latex?f%28x_4%29%20%5Csim%20N%280%2C%20k%28x_4%2Cx_4%29%29%20%3D%20N%280%2C1%29 "f(x_4) \sim N(0, k(x_4,x_4)) = N(0,1)")

假设四个数据的建模为随机变量f_new

![\bold f\_{new} = \begin{bmatrix} 
f(x_1) \\f(x_2) \\f(x_3)  \\f\_\*(x_4)  \end{bmatrix} \sim N(\mu, K) =N(\begin{bmatrix} 
0 \\0 \\0\\0\end{bmatrix} ,\begin{bmatrix} 
k\_{11}&k\_{12}&k\_{13} &k\_{14} \\k\_{21}&k\_{22}&k\_{23}&k\_{24}\\k\_{31}&k\_{32}&k\_{33}&k\_{34}\\k\_{41}&k\_{42}&k\_{43}&k\_{44}\end{bmatrix}) \sim N(0,\begin{bmatrix} 
K &K\_{4}\\K\_{4}^T&K\_{44}\end{bmatrix})](https://latex.codecogs.com/svg.latex?%5Cbold%20f_%7Bnew%7D%20%3D%20%5Cbegin%7Bbmatrix%7D%20%0Af%28x_1%29%20%5C%5Cf%28x_2%29%20%5C%5Cf%28x_3%29%20%20%5C%5Cf_%2A%28x_4%29%20%20%5Cend%7Bbmatrix%7D%20%5Csim%20N%28%5Cmu%2C%20K%29%20%3DN%28%5Cbegin%7Bbmatrix%7D%20%0A0%20%5C%5C0%20%5C%5C0%5C%5C0%5Cend%7Bbmatrix%7D%20%2C%5Cbegin%7Bbmatrix%7D%20%0Ak_%7B11%7D%26k_%7B12%7D%26k_%7B13%7D%20%26k_%7B14%7D%20%5C%5Ck_%7B21%7D%26k_%7B22%7D%26k_%7B23%7D%26k_%7B24%7D%5C%5Ck_%7B31%7D%26k_%7B32%7D%26k_%7B33%7D%26k_%7B34%7D%5C%5Ck_%7B41%7D%26k_%7B42%7D%26k_%7B43%7D%26k_%7B44%7D%5Cend%7Bbmatrix%7D%29%20%5Csim%20N%280%2C%5Cbegin%7Bbmatrix%7D%20%0AK%20%26K_%7B4%7D%5C%5CK_%7B4%7D%5ET%26K_%7B44%7D%5Cend%7Bbmatrix%7D%29 "\bold f_{new} = \begin{bmatrix} 
f(x_1) \\f(x_2) \\f(x_3)  \\f_*(x_4)  \end{bmatrix} \sim N(\mu, K) =N(\begin{bmatrix} 
0 \\0 \\0\\0\end{bmatrix} ,\begin{bmatrix} 
k_{11}&k_{12}&k_{13} &k_{14} \\k_{21}&k_{22}&k_{23}&k_{24}\\k_{31}&k_{32}&k_{33}&k_{34}\\k_{41}&k_{42}&k_{43}&k_{44}\end{bmatrix}) \sim N(0,\begin{bmatrix} 
K &K_{4}\\K_{4}^T&K_{44}\end{bmatrix})")

并且有

![K_4 = k(x_i,x_4)](https://latex.codecogs.com/svg.latex?K_4%20%3D%20k%28x_i%2Cx_4%29 "K_4 = k(x_i,x_4)")

![K\_{44} = k(x_4,x_4)](https://latex.codecogs.com/svg.latex?K_%7B44%7D%20%3D%20k%28x_4%2Cx_4%29 "K_{44} = k(x_4,x_4)")

就有

![\begin{bmatrix} 
f \\f\_\*(x_4)  \end{bmatrix}\sim N(0,\begin{bmatrix} 
K &K\_{4}\\K\_{4}^T&K\_{44}\end{bmatrix})](https://latex.codecogs.com/svg.latex?%5Cbegin%7Bbmatrix%7D%20%0Af%20%5C%5Cf_%2A%28x_4%29%20%20%5Cend%7Bbmatrix%7D%5Csim%20N%280%2C%5Cbegin%7Bbmatrix%7D%20%0AK%20%26K_%7B4%7D%5C%5CK_%7B4%7D%5ET%26K_%7B44%7D%5Cend%7Bbmatrix%7D%29 "\begin{bmatrix} 
f \\f_*(x_4)  \end{bmatrix}\sim N(0,\begin{bmatrix} 
K &K_{4}\\K_{4}^T&K_{44}\end{bmatrix})")

根据多元变量的高斯分布，

![p(f\_\*(x_4)\|x_4,x,f) = N(f\_\*(x_4)\|\mu_4, \Sigma_4)](https://latex.codecogs.com/svg.latex?p%28f_%2A%28x_4%29%7Cx_4%2Cx%2Cf%29%20%3D%20N%28f_%2A%28x_4%29%7C%5Cmu_4%2C%20%5CSigma_4%29 "p(f_*(x_4)|x_4,x,f) = N(f_*(x_4)|\mu_4, \Sigma_4)")

![\mu_4 = K_4^TK^{-1}f](https://latex.codecogs.com/svg.latex?%5Cmu_4%20%3D%20K_4%5ETK%5E%7B-1%7Df "\mu_4 = K_4^TK^{-1}f")

![\Sigma_4 = K\_{44} - K_4^TK^{-1}K\_{4}](https://latex.codecogs.com/svg.latex?%5CSigma_4%20%3D%20K_%7B44%7D%20-%20K_4%5ETK%5E%7B-1%7DK_%7B4%7D "\Sigma_4 = K_{44} - K_4^TK^{-1}K_{4}")

这样就求出![f\_\*(x_4)](https://latex.codecogs.com/svg.latex?f_%2A%28x_4%29 "f_*(x_4)")的分布了。

![gp_2.png](../../../img/20231207/kernel.png)

如果观测样本是有噪声的，那么可以用![y = f + \epsilon](https://latex.codecogs.com/svg.latex?y%20%3D%20f%20%2B%20%5Cepsilon "y = f + \epsilon")，即观测值 `y` 可以被看作是真实值 `f` 加上随机误差 `\epsilon` 。

计算的步骤也是一样，计算公式为

![p(f\_\*(x_4)\|x_4,x,f) = N(f\_\*(x_4)\|\mu_4, \Sigma_4)](https://latex.codecogs.com/svg.latex?p%28f_%2A%28x_4%29%7Cx_4%2Cx%2Cf%29%20%3D%20N%28f_%2A%28x_4%29%7C%5Cmu_4%2C%20%5CSigma_4%29 "p(f_*(x_4)|x_4,x,f) = N(f_*(x_4)|\mu_4, \Sigma_4)")

![\mu_4 = K_4^TK_y^{-1}f](https://latex.codecogs.com/svg.latex?%5Cmu_4%20%3D%20K_4%5ETK_y%5E%7B-1%7Df "\mu_4 = K_4^TK_y^{-1}f")

![\Sigma_4 = K\_{44} - K_4^TK_y^{-1}K\_{4}](https://latex.codecogs.com/svg.latex?%5CSigma_4%20%3D%20K_%7B44%7D%20-%20K_4%5ETK_y%5E%7B-1%7DK_%7B4%7D "\Sigma_4 = K_{44} - K_4^TK_y^{-1}K_{4}")

![K_y = K + \sigma_y^2I](https://latex.codecogs.com/svg.latex?K_y%20%3D%20K%20%2B%20%5Csigma_y%5E2I "K_y = K + \sigma_y^2I")
