from dataclasses import dataclass
import torch

@dataclass
class ChunkTask:
    chunk_id: int
    content_length: int
    start: int
    end_exclusive: int

@dataclass
class PlannedStage:
    stage_id: int
    prefix: torch.Tensor
    full_sequence: torch.Tensor
    attention_mask: torch.Tensor
    tasks: list[ChunkTask]
    diffusion_steps: int
    terminator_token_id: int