"""Audio-clock helpers for seamless MiniMax H3 segment assembly."""

from __future__ import annotations

import math

import torch


H3_VIDEO_FPS = 24
H3_AUDIO_LATENT_FPS = 40


def audio_ticks_for_rgb_frames(frame_count: int) -> int:
    """Map an exact RGB duration to MiniMax H3's 40 Hz audio clock."""

    frames = int(frame_count)
    if frames < 0:
        raise ValueError("frame_count cannot be negative")
    return round(frames * H3_AUDIO_LATENT_FPS / H3_VIDEO_FPS)


def equal_power_crossfade(
    left: torch.Tensor,
    right: torch.Tensor,
    overlap_samples: int,
) -> torch.Tensor:
    """Join PCM tensors with a peak-safe, equal-power-derived crossfade.

    Normalizing the sine/cosine weights by their sum prevents the +3 dB peak
    that a raw equal-power curve produces when the overlapping audio is highly
    correlated, as continuation audio normally is.
    """

    if not torch.is_tensor(left) or not torch.is_tensor(right):
        raise ValueError("left and right audio must be tensors")
    if left.ndim < 1 or right.ndim < 1 or left.shape[:-1] != right.shape[:-1]:
        raise ValueError("left and right audio must have matching batch and channel dimensions")
    overlap = int(overlap_samples)
    if overlap < 0:
        raise ValueError("overlap_samples cannot be negative")
    if overlap > left.shape[-1] or overlap > right.shape[-1]:
        raise ValueError("overlap_samples must fit both audio tensors")

    right = right.to(device=left.device, dtype=left.dtype)
    if overlap == 0:
        return torch.cat((left, right), dim=-1)
    if overlap == 1:
        fade_in = torch.full((1,), math.sqrt(0.5), device=left.device, dtype=left.dtype)
    else:
        phase = torch.linspace(
            0.0, math.pi / 2.0, overlap,
            device=left.device, dtype=left.dtype,
        )
        fade_in = torch.sin(phase)
    fade_out = torch.sqrt(torch.clamp(1.0 - fade_in.square(), min=0.0))
    weight_sum = fade_in + fade_out
    fade_in = fade_in / weight_sum
    fade_out = fade_out / weight_sum
    shape = (1,) * (left.ndim - 1) + (overlap,)
    blended = left[..., -overlap:] * fade_out.reshape(shape)
    blended = blended + right[..., :overlap] * fade_in.reshape(shape)
    return torch.cat((left[..., :-overlap], blended, right[..., overlap:]), dim=-1)
