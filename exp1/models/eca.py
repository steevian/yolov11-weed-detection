# -*- coding: utf-8 -*-
from __future__ import annotations

import torch
import torch.nn as nn


class ECA(nn.Module):
    """Efficient Channel Attention.

    This module is lightweight and suitable for inserting after feature maps P3/P4/P5.
    """

    def __init__(self, k_size: int = 3) -> None:
        super().__init__()
        if k_size % 2 == 0:
            k_size += 1
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv = nn.Conv1d(1, 1, kernel_size=k_size, padding=(k_size - 1) // 2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.avg_pool(x)
        y = self.conv(y.squeeze(-1).transpose(-1, -2))
        y = self.sigmoid(y.transpose(-1, -2).unsqueeze(-1))
        return x * y.expand_as(x)
