---
title:  "2023-11-20 论文 Uncertainty Quantification in Machine Learning for Engineering Design and Health Prognostics"
date: 2023-11-20T18:31:50+08:00  
tags: ["tech","bayesian"]
format: hugo-md
isCJKLanguage: true
html-math-method: webtex
# thumbnail: https://picsum.photos/id/310/400/250
---




Abstract

- types
    - 第一种分类
        - data uncertainty (measurement noise)
        - model uncertainty ( limited data)
    - 第二种分类
        - epistemic uncertainty
            - 认知上的不确定性，通常是由于没有足够的知识（数据）而产生
            - can be reducible
            - 分为两类
                - model-form uncertainty
                    - 由于模型的选择导致，例如architectures, activation functions or kernel functions
                - parameter uncertainty
                    - 在训练过程产生，由于数据不够导致
        - aleatory uncertainty
            - stems from physical systems, 具有随机性, cannot be reducible
            - e.g. noises
            - 这种类型的不确定性在ML模型里面被看成是似然函数的一部分(a part of the likelihood function)
            - 也被叫做data uncertainty
            - 捕捉这种不确定性的方式有：同方差 homoscedastic和异方差 heteroscedastic
        - 例子：
            - test data和train data不同分布：epistemic uncertainty (model performs poorer in extrapolation than in interpolation)
            - 测量数据由仪器导致的误差是aleatory Unc， 大试如果由于精度原因导致，则属于epistemic unc，因为提高精度可以减少这个误差
        - 
- causes
- methods:
    - Gaussian process regression
        - a ML method with UQ capability
        - 一般不用来quantify uncertainty of a final surrogate
        - 一般用来在高度不确定的采样空间里采样，来减少训练样本的数量
            - to build an accurate surrogate within some lower and upper bounds of input variables
            - to find a globally optimally design for black-box objective function
        - 一般不评估GPR的UQ质量
            - 因为预测一般在pre-defined design bounds
    - Bayesian neural network
        - Monte Carlo dropout as an alternative to traditional Bayesian neural network
    - neural network ensemble
        - neural network ensemble consisting of multiple neural networks
    - deterministic UQ methods
- metrics
    - classification
        - probability can be viewed as uncertainty
    - regression
        - confidence interval :
            - 没看懂： prediction may be 120 ± 15, in weeks, which represents a two-sided 95% confidence interval (i.e.,∼1.96 standard deviations subtracted from or added to the mean estimate assuming the model-predicted RUL follows a Gaussian distribution).