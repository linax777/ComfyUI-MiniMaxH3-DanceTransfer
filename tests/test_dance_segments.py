from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(
    os.environ.get("DANCE_PROJECT_ROOT", Path(__file__).resolve().parents[1])
)
MODULE_PATH = PROJECT_ROOT / "dance_continuation.py"


def load_dance_module():
    spec = importlib.util.spec_from_file_location("dance_continuation", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("duration_seconds", "expected_ranges"),
    [
        (10, [(0, 240, 0, 240, 0)]),
        (
            30,
            [
                (0, 243, 0, 243, 0),
                (219, 462, 243, 462, 24),
                (438, 681, 462, 681, 24),
                (657, 720, 681, 720, 24),
            ],
        ),
        (
            60,
            [
                (0, 243, 0, 243, 0),
                (219, 462, 243, 462, 24),
                (438, 681, 462, 681, 24),
                (657, 900, 681, 900, 24),
                (876, 1119, 900, 1119, 24),
                (1095, 1338, 1119, 1338, 24),
                (1314, 1440, 1338, 1440, 24),
            ],
        ),
    ],
)
def test_dance_segments_cover_source_without_drift(duration_seconds, expected_ranges):
    dance = load_dance_module()

    report = dance.build_dance_segment_report(
        total_source_frames=duration_seconds * 24,
        segment_frames=243,
        requested_context_frames=24,
    )

    assert [
        (
            item.source_start_frame,
            item.source_end_frame,
            item.output_start_frame,
            item.output_end_frame,
            item.requested_context_frames,
        )
        for item in report
    ] == expected_ranges
    assert report[-1].output_end_frame == duration_seconds * 24
    assert [item.source_start_frame for item in report] == sorted(
        item.source_start_frame for item in report
    )
    for previous, current in zip(report, report[1:]):
        assert previous.source_end_frame - current.source_start_frame == 24
        assert previous.output_end_frame == current.output_start_frame


def test_requested_rgb_context_is_distinct_from_h3_alignment():
    dance = load_dance_module()

    report = dance.build_dance_segment_report(720, 243, 24)

    assert report[1].requested_context_frames == 24
    assert report[1].aligned_context_frames == 22
    assert report[1].context_latent_ticks == 7


def test_dance_segment_debug_format_is_machine_readable():
    dance = load_dance_module()
    report = dance.build_dance_segment_report(720, 243, 24)

    assert dance.format_dance_segment_debug(report[0]) == (
        "[DANCE] segment=1 source=0:243 output=0:243 "
        "requested_context=0 aligned_context=0 latent_ticks=0"
    )
    assert dance.format_dance_segment_debug(report[1]) == (
        "[DANCE] segment=2 source=219:462 output=243:462 "
        "requested_context=24 aligned_context=22 latent_ticks=7"
    )


@pytest.mark.parametrize(
    ("total_frames", "segment_frames", "context_frames", "message"),
    [
        (0, 243, 24, "total_source_frames"),
        (720, 0, 24, "segment_frames"),
        (720, 243, -1, "requested_context_frames"),
        (720, 24, 24, "shorter than segment_frames"),
    ],
)
def test_dance_segment_report_rejects_invalid_ranges(
    total_frames, segment_frames, context_frames, message
):
    dance = load_dance_module()

    with pytest.raises(ValueError, match=message):
        dance.build_dance_segment_report(total_frames, segment_frames, context_frames)
