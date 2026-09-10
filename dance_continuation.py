"""Pure dance-continuation planning helpers.

This module intentionally has no ComfyUI or model imports so its frame
arithmetic can be tested without loading H3 weights.
"""

from __future__ import annotations

from dataclasses import dataclass


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
    )


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
