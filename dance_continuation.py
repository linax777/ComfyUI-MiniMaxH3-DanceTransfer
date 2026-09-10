"""Pure dance-continuation planning helpers.

This module intentionally has no ComfyUI or model imports so its frame
arithmetic can be tested without loading H3 weights.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
import torch.nn.functional as F


@dataclass(frozen=True)
class DanceSegmentDebug:
    segment_index: int
    source_start_frame: int
    source_end_frame: int
    output_start_frame: int
    output_end_frame: int
    requested_context_frames: int
    aligned_context_frames: int
    context_latent_ticks: int


@dataclass(frozen=True)
class DanceContinuationConfig:
    enabled: bool = False
    context_frames: int = 24
    taper_enabled: bool = False
    taper_frames: int = 12
    start_strength: float = 1.0
    end_strength: float = 0.0
    context_noise_enabled: bool = False
    context_noise_strength: float = 0.0
    context_noise_taper_frames: int = 4

    def __post_init__(self) -> None:
        if self.context_frames < 0:
            raise ValueError("context_frames cannot be negative")
        if self.taper_frames < 0:
            raise ValueError("taper_frames cannot be negative")
        if self.taper_frames > self.context_frames:
            raise ValueError("taper_frames cannot exceed context_frames")
        if not 0.0 <= self.start_strength <= 1.0:
            raise ValueError("start_strength must be in [0, 1]")
        if not 0.0 <= self.end_strength <= 1.0:
            raise ValueError("end_strength must be in [0, 1]")
        if not 0.0 <= self.context_noise_strength <= 1.0:
            raise ValueError("context_noise_strength must be in [0, 1]")
        if self.context_noise_taper_frames < 0:
            raise ValueError("context_noise_taper_frames cannot be negative")
        if self.context_noise_taper_frames > self.context_frames:
            raise ValueError(
                "context_noise_taper_frames cannot exceed context_frames"
            )


@dataclass(frozen=True)
class DanceContextTiming:
    source_overlap_frames: int
    output_trim_frames: int
    aligned_context_frames: int
    context_latent_ticks: int


def parse_dance_continuation(timeline: object) -> DanceContinuationConfig:
    """Parse version-tolerant dance configuration from timeline JSON."""

    timeline_data = timeline if isinstance(timeline, dict) else {}
    raw = timeline_data.get("danceContinuation")
    values = raw if isinstance(raw, dict) else {}
    return DanceContinuationConfig(
        enabled=bool(values.get("enabled", False)),
        context_frames=int(values.get("contextFrames", 24)),
        taper_enabled=bool(values.get("taperEnabled", False)),
        taper_frames=int(values.get("taperFrames", 12)),
        start_strength=float(values.get("startStrength", 1.0)),
        end_strength=float(values.get("endStrength", 0.0)),
        context_noise_enabled=bool(values.get("contextNoiseEnabled", False)),
        context_noise_strength=float(values.get("contextNoiseStrength", 0.0)),
        context_noise_taper_frames=int(values.get("contextNoiseTaperFrames", 4)),
    )


def extract_tail_frames(frames: Any, frame_count: int) -> Any:
    """Return a detached working copy of the last requested clean frames."""

    requested = int(frame_count)
    if requested <= 0:
        return frames[:0].clone()
    available = int(frames.shape[0])
    return frames[-min(requested, available) :].clone()


def apply_deterministic_context_noise(
    clean_source: torch.Tensor,
    strength: float,
    taper_steps: int,
    seed: int,
    *,
    time_dim: int = 0,
) -> torch.Tensor:
    """Add reproducible noise to a disposable clone of continuity context."""

    amount = float(strength)
    taper = int(taper_steps)
    if not 0.0 <= amount <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    if taper < 0:
        raise ValueError("taper_steps cannot be negative")
    if clean_source.ndim == 0:
        raise ValueError("clean_source must have a temporal dimension")
    resolved_dim = int(time_dim) % clean_source.ndim
    step_count = int(clean_source.shape[resolved_dim])
    if taper > step_count:
        raise ValueError("taper_steps cannot exceed the temporal length")

    continuity_working_copy = clean_source.clone()
    if amount == 0.0 or continuity_working_copy.numel() == 0:
        return continuity_working_copy

    generator = torch.Generator(device=continuity_working_copy.device)
    generator.manual_seed(int(seed) & 0xFFFFFFFFFFFFFFFF)
    noise = torch.randn(
        continuity_working_copy.shape,
        dtype=continuity_working_copy.dtype,
        device=continuity_working_copy.device,
        generator=generator,
    )
    weights = torch.full(
        (step_count,), amount,
        dtype=continuity_working_copy.dtype,
        device=continuity_working_copy.device,
    )
    if taper > 0:
        weights[-taper:] = torch.linspace(
            amount, 0.0, steps=taper,
            dtype=weights.dtype, device=weights.device,
        )
    shape = [1] * continuity_working_copy.ndim
    shape[resolved_dim] = step_count
    return continuity_working_copy + noise * weights.reshape(shape)


def align_h3_context_frames(requested_frames: int) -> int:
    """Align an RGB duration down to H3's legal 1 or ``17*k+5`` grid."""

    requested = int(requested_frames)
    if requested <= 0:
        return 0
    if requested < 5:
        return 1
    return requested - ((requested - 5) % 17)


def rgb_frames_to_h3_latent_ticks(requested_frames: int) -> int:
    """Return the video-token count for an RGB context duration."""

    aligned = align_h3_context_frames(requested_frames)
    if aligned <= 0:
        return 0
    return 2 if aligned <= 5 else ((aligned - 5) // 17) * 5 + 2


def resolve_context_timing(
    config: DanceContinuationConfig, legacy_requested_overlap: int
) -> DanceContextTiming:
    """Resolve exact RGB timing separately from H3 latent alignment."""

    requested = (
        config.context_frames if config.enabled else int(legacy_requested_overlap)
    )
    aligned = align_h3_context_frames(requested)
    source_overlap = requested if config.enabled else aligned
    return DanceContextTiming(
        source_overlap_frames=source_overlap,
        output_trim_frames=source_overlap,
        aligned_context_frames=aligned,
        context_latent_ticks=rgb_frames_to_h3_latent_ticks(requested),
    )


def build_linear_context_strength(
    context_frames: int,
    taper_frames: int,
    start_strength: float,
    end_strength: float,
) -> torch.Tensor:
    """Build per-RGB-frame continuity strength with a final linear release."""

    context = int(context_frames)
    taper = int(taper_frames)
    start = float(start_strength)
    end = float(end_strength)
    if context < 0:
        raise ValueError("context_frames cannot be negative")
    if taper < 0 or taper > context:
        raise ValueError("taper_frames must be in [0, context_frames]")
    if not 0.0 <= start <= 1.0:
        raise ValueError("start_strength must be in [0, 1]")
    if not 0.0 <= end <= 1.0:
        raise ValueError("end_strength must be in [0, 1]")
    if context == 0:
        return torch.empty(0, dtype=torch.float32)
    if taper == 0:
        return torch.full((context,), start, dtype=torch.float32)

    held = torch.full((context - taper,), start, dtype=torch.float32)
    release = torch.linspace(start, end, steps=taper, dtype=torch.float32)
    return torch.cat((held, release))


def context_strength_to_latent_mask(
    rgb_strength: torch.Tensor, latent_ticks: int
) -> torch.Tensor:
    """Resample RGB continuity strength into H3 latent noise-mask ticks."""

    if rgb_strength.ndim != 1:
        raise ValueError("rgb_strength must be a one-dimensional tensor")
    ticks = int(latent_ticks)
    if rgb_strength.numel() == 0:
        if ticks != 0:
            raise ValueError("empty rgb_strength requires latent_ticks=0")
        return rgb_strength.clone().to(dtype=torch.float32)
    if ticks <= 0:
        raise ValueError("latent_ticks must be positive for nonempty rgb_strength")
    sampled_strength = F.interpolate(
        rgb_strength.to(dtype=torch.float32).reshape(1, 1, -1),
        size=ticks,
        mode="linear",
        align_corners=True,
    ).reshape(-1)
    return (1.0 - sampled_strength).clamp_(0.0, 1.0)


def format_dance_segment_debug(segment: DanceSegmentDebug) -> str:
    """Format stable, grep-friendly segment timing diagnostics."""

    return (
        f"[DANCE] segment={segment.segment_index + 1} "
        f"source={segment.source_start_frame}:{segment.source_end_frame} "
        f"output={segment.output_start_frame}:{segment.output_end_frame} "
        f"requested_context={segment.requested_context_frames} "
        f"aligned_context={segment.aligned_context_frames} "
        f"latent_ticks={segment.context_latent_ticks}"
    )


def build_dance_segment_report(
    total_source_frames: int,
    segment_frames: int,
    requested_context_frames: int,
) -> tuple[DanceSegmentDebug, ...]:
    """Plan source windows and deduplicated output coverage without drift."""

    total = int(total_source_frames)
    segment = int(segment_frames)
    context = int(requested_context_frames)
    if total <= 0:
        raise ValueError("total_source_frames must be greater than zero")
    if segment <= 0:
        raise ValueError("segment_frames must be greater than zero")
    if context < 0:
        raise ValueError("requested_context_frames cannot be negative")
    if context >= segment:
        raise ValueError("requested_context_frames must be shorter than segment_frames")

    aligned = align_h3_context_frames(context)
    ticks = rgb_frames_to_h3_latent_ticks(context)
    stride = segment - context
    report: list[DanceSegmentDebug] = []
    source_start = 0
    output_start = 0
    index = 0
    while source_start < total:
        source_end = min(total, source_start + segment)
        current_context = 0 if index == 0 else min(context, source_end - source_start)
        current_output_start = output_start
        current_output_end = source_end
        report.append(
            DanceSegmentDebug(
                segment_index=index,
                source_start_frame=source_start,
                source_end_frame=source_end,
                output_start_frame=current_output_start,
                output_end_frame=current_output_end,
                requested_context_frames=current_context,
                aligned_context_frames=0 if index == 0 else aligned,
                context_latent_ticks=0 if index == 0 else ticks,
            )
        )
        if source_end >= total:
            break
        output_start = source_end
        source_start += stride
        index += 1
    return tuple(report)
