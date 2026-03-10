"""Efficient Channel Attention (ECA) module."""

from __future__ import annotations

import math

import torch
import torch.nn as nn


class ECA(nn.Module):
    """ECA: GAP + 1D Conv + Sigmoid channel reweighting."""

    def __init__(self, k_size: int = 3, gamma: int = 2, b: int = 1):
        super().__init__()
        if k_size <= 0:
            raise ValueError("k_size must be > 0")
        if k_size % 2 == 0:
            k_size += 1

        self.gamma = gamma
        self.b = b
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv = nn.Conv1d(1, 1, kernel_size=k_size, padding=(k_size - 1) // 2, bias=False)
        self.sigmoid = nn.Sigmoid()

    @staticmethod
    def auto_kernel(channels: int, gamma: int = 2, b: int = 1) -> int:
        t = int(abs((math.log2(channels) + b) / gamma))
        k = t if t % 2 else t + 1
        return max(k, 3)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.avg_pool(x)
        y = y.squeeze(-1).transpose(-1, -2)
        y = self.conv(y)
        y = y.transpose(-1, -2).unsqueeze(-1)
        y = self.sigmoid(y)
        return x * y.expand_as(x)
