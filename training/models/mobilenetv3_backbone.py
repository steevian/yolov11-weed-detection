"""MobileNetV3 backbone adapter for custom YOLO experiments.

This module is provided as a standalone implementation for research and ablation.
The phase3 YAML in this repository uses Ultralytics built-in TorchVision+Index
for maximum compatibility, while this class can be integrated into a patched
Ultralytics parser if needed.
"""

from __future__ import annotations

from typing import Sequence

import torch
import torch.nn as nn
import torchvision


class MobileNetV3Backbone(nn.Module):
    """Return P3/P4/P5-style feature maps from MobileNetV3-Large."""

    def __init__(
        self,
        out_channels: Sequence[int] = (256, 512, 1024),
        pretrained: bool = True,
        feature_indices: Sequence[int] = (4, 8, 12),
    ):
        super().__init__()
        weights = torchvision.models.MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
        model = torchvision.models.mobilenet_v3_large(weights=weights)
        self.features = model.features
        self.feature_indices = tuple(feature_indices)

        # Approximate channels at selected feature taps for mobilenet_v3_large.
        in_channels = (40, 112, 960)
        self.adapters = nn.ModuleList(
            [nn.Conv2d(cin, cout, kernel_size=1, stride=1, padding=0) for cin, cout in zip(in_channels, out_channels)]
        )

    def forward(self, x: torch.Tensor) -> list[torch.Tensor]:
        outs = []
        for i, block in enumerate(self.features):
            x = block(x)
            if i in self.feature_indices:
                outs.append(x)

        if len(outs) != 3:
            raise RuntimeError(f"Expected 3 feature maps, got {len(outs)}")

        p3 = self.adapters[0](outs[0])
        p4 = self.adapters[1](outs[1])
        p5 = self.adapters[2](outs[2])
        return [p3, p4, p5]
