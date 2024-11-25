from __future__ import annotations

from typing import Optional

import torch
from core.utils import xor_not_none
from pydantic import model_validator
from pydantic.dataclasses import dataclass


@dataclass
class ModelInput:
    video: Optional[torch.Tensor] = None
    other_video: Optional[torch.Tensor] = None
    video_embedding: Optional[torch.Tensor] = None
    other_video_embedding: Optional[torch.Tensor] = None

    @model_validator(mode="after")
    def check_specified_videos_consistency(self) -> ModelInput:
        if xor_not_none(self.video, self.video_embedding) is False:
            raise ValueError(
                "Either 'video' or 'video_embedding' must be specified, and not both"
            )

        if xor_not_none(self.other_video, self.other_video_embedding) is False:
            raise ValueError(
                "Either 'other_video' or 'other_video_embedding' must be specified, "
                "and not both"
            )

        return self
