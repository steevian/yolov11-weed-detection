# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List

import torch
import torch.nn as nn
from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large


class MobileNetV3Backbone(nn.Module):
    """MobileNetV3-Large backbone wrapper.

    Returns three pyramid features aligned with P3/P4/P5 semantics.
    This class is provided for thesis artifact completeness and can be registered
    into Ultralytics custom module scope when needed.
    """

    def __init__(self, pretrained: bool = True) -> None:
        super().__init__()
        weights = MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
        model = mobilenet_v3_large(weights=weights)
        self.features = model.features
        self.out_indices = [5, 12, 16]  # consistent with MBV3 stage boundaries

    def forward(self, x: torch.Tensor) -> List[torch.Tensor]:
        outs: List[torch.Tensor] = []
        for i, block in enumerate(self.features):
            x = block(x)
            if i in self.out_indices:
                outs.append(x)
        return outs
