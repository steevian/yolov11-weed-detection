"""SimAM attention module for exp2 ablation.

This implementation is parameter-free and suitable for lightweight insertion.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class SimAM(nn.Module):
    """Simple, parameter-free attention module.

    Paper: SimAM: A Simple, Parameter-Free Attention Module for Convolutional Neural Networks
    """

    def __init__(self, e_lambda: float = 1e-4) -> None:
        super().__init__()
        self.e_lambda = e_lambda

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # 中文注释：按论文公式计算每个神经元的重要性权重，不引入可训练参数。
        n = x.shape[2] * x.shape[3] - 1
        mu = x.mean(dim=(2, 3), keepdim=True)
        d = (x - mu).pow(2)
        v = d.sum(dim=(2, 3), keepdim=True) / max(n, 1)
        e_inv = d / (4 * (v + self.e_lambda)) + 0.5
        return x * torch.sigmoid(e_inv)
