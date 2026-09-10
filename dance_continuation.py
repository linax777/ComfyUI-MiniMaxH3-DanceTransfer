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
