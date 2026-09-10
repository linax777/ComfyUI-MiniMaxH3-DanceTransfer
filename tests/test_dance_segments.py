from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest
import torch


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


def test_old_workflow_defaults_to_disabled_dance_continuation():
    dance = load_dance_module()

    config = dance.parse_dance_continuation({"selection": {"start": 0}})

    assert config == dance.DanceContinuationConfig()
    assert config.enabled is False
    assert config.context_frames == 24
    assert config.taper_enabled is False
    assert config.taper_frames == 12
    assert config.start_strength == 1.0
    assert config.end_strength == 0.0


def test_dance_continuation_parses_serialized_values():
    dance = load_dance_module()

    config = dance.parse_dance_continuation(
        {
            "danceContinuation": {
                "enabled": True,
                "contextFrames": 30,
                "taperEnabled": True,
                "taperFrames": 18,
                "startStrength": 0.8,
                "endStrength": 0.2,
            }
        }
    )

    assert config == dance.DanceContinuationConfig(
        enabled=True,
        context_frames=30,
        taper_enabled=True,
        taper_frames=18,
        start_strength=0.8,
        end_strength=0.2,
    )


def test_experimental_context_noise_parses_off_by_default_and_when_enabled():
    dance = load_dance_module()

    default = dance.parse_dance_continuation({})
    enabled = dance.parse_dance_continuation({
        "danceContinuation": {
            "contextNoiseEnabled": True,
            "contextNoiseStrength": 0.3,
            "contextNoiseTaperFrames": 4,
        }
    })

    assert default.context_noise_enabled is False
    assert default.context_noise_strength == 0.0
    assert default.context_noise_taper_frames == 4
    assert enabled.context_noise_enabled is True
    assert enabled.context_noise_strength == 0.3
    assert enabled.context_noise_taper_frames == 4


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"contextFrames": -1}, "context_frames"),
        ({"contextFrames": 4, "taperFrames": 5}, "taper_frames"),
        ({"taperFrames": -1}, "taper_frames"),
        ({"startStrength": -0.01}, "start_strength"),
        ({"startStrength": 1.01}, "start_strength"),
        ({"endStrength": -0.01}, "end_strength"),
        ({"endStrength": 1.01}, "end_strength"),
        ({"contextNoiseStrength": -0.01}, "context_noise_strength"),
        ({"contextNoiseStrength": 1.01}, "context_noise_strength"),
        ({"contextNoiseTaperFrames": -1}, "context_noise_taper_frames"),
        ({"contextNoiseTaperFrames": 25}, "context_noise_taper_frames"),
    ],
)
def test_dance_continuation_rejects_invalid_values(values, message):
    dance = load_dance_module()

    with pytest.raises(ValueError, match=message):
        dance.parse_dance_continuation({"danceContinuation": values})


@pytest.mark.parametrize(
    ("source_count", "requested_count", "expected"),
    [
        (10, 24, list(range(10))),
        (24, 24, list(range(24))),
        (30, 24, list(range(6, 30))),
        (30, 0, []),
    ],
)
def test_extract_tail_frames_returns_clean_bounded_clone(
    source_count, requested_count, expected
):
    dance = load_dance_module()
    previous_clean_output = torch.arange(source_count, dtype=torch.float32).reshape(
        source_count, 1
    )
    original = previous_clean_output.clone()

    continuity_working_copy = dance.extract_tail_frames(
        previous_clean_output, requested_count
    )

    assert continuity_working_copy[:, 0].tolist() == expected
    assert torch.equal(previous_clean_output, original)
    assert continuity_working_copy.data_ptr() != previous_clean_output.data_ptr()


def test_mutating_continuation_copy_never_changes_clean_output():
    dance = load_dance_module()
    previous_clean_output = torch.arange(30, dtype=torch.float32).reshape(30, 1)
    original = previous_clean_output.clone()

    continuity_working_copy = dance.extract_tail_frames(previous_clean_output, 24)
    continuity_working_copy.zero_()

    assert torch.equal(previous_clean_output, original)


def test_context_noise_is_deterministic_and_never_mutates_clean_source():
    dance = load_dance_module()
    previous_clean_output = torch.ones((7, 2), dtype=torch.float32)
    original = previous_clean_output.clone()

    first = dance.apply_deterministic_context_noise(
        previous_clean_output, strength=0.2, taper_steps=3, seed=1234,
    )
    second = dance.apply_deterministic_context_noise(
        previous_clean_output, strength=0.2, taper_steps=3, seed=1234,
    )
    different_segment = dance.apply_deterministic_context_noise(
        previous_clean_output, strength=0.2, taper_steps=3, seed=1235,
    )

    assert torch.equal(first, second)
    assert not torch.equal(first, different_segment)
    assert torch.equal(previous_clean_output, original)
    assert first.data_ptr() != previous_clean_output.data_ptr()
    assert torch.equal(first[-1], previous_clean_output[-1])


def test_disabled_context_noise_returns_an_independent_copy():
    dance = load_dance_module()
    source = torch.arange(8, dtype=torch.float32).reshape(4, 2)

    result = dance.apply_deterministic_context_noise(
        source, strength=0.0, taper_steps=4, seed=1,
    )

    assert torch.equal(result, source)
    assert result.data_ptr() != source.data_ptr()


def test_enabled_dance_timing_keeps_requested_rgb_and_aligned_latent_separate():
    dance = load_dance_module()
    config = dance.DanceContinuationConfig(enabled=True, context_frames=24)

    timing = dance.resolve_context_timing(config, legacy_requested_overlap=48)

    assert timing.source_overlap_frames == 24
    assert timing.output_trim_frames == 24
    assert timing.aligned_context_frames == 22
    assert timing.context_latent_ticks == 7


def test_disabled_dance_timing_reproduces_legacy_overlap_alignment():
    dance = load_dance_module()
    config = dance.DanceContinuationConfig(enabled=False)

    timing = dance.resolve_context_timing(config, legacy_requested_overlap=48)

    assert timing.source_overlap_frames == 39
    assert timing.output_trim_frames == 39
    assert timing.aligned_context_frames == 39
    assert timing.context_latent_ticks == 12


@pytest.mark.parametrize(
    ("requested_rgb_frames", "aligned_rgb_frames", "latent_ticks"),
    [(12, 5, 2), (18, 5, 2), (22, 22, 7), (24, 22, 7),
     (30, 22, 7), (36, 22, 7), (39, 39, 12)],
)
def test_rgb_context_sweep_preserves_request_while_deriving_h3_ticks(
    requested_rgb_frames, aligned_rgb_frames, latent_ticks
):
    dance = load_dance_module()

    assert dance.align_h3_context_frames(requested_rgb_frames) == aligned_rgb_frames
    assert dance.rgb_frames_to_h3_latent_ticks(requested_rgb_frames) == latent_ticks


def test_linear_context_strength_holds_then_releases():
    dance = load_dance_module()

    strength = dance.build_linear_context_strength(24, 12, 1.0, 0.0)

    assert strength.shape == (24,)
    assert torch.equal(strength[:12], torch.ones(12))
    assert strength[12].item() == pytest.approx(1.0)
    assert strength[-1].item() == pytest.approx(0.0)
    assert torch.all(strength[1:] <= strength[:-1])
    assert torch.all((strength >= 0.0) & (strength <= 1.0))


def test_zero_taper_keeps_start_strength_constant():
    dance = load_dance_module()

    strength = dance.build_linear_context_strength(5, 0, 0.7, 0.2)

    assert torch.allclose(strength, torch.full((5,), 0.7))


def test_zero_context_returns_empty_strength_tensor():
    dance = load_dance_module()

    assert dance.build_linear_context_strength(0, 0, 1.0, 0.0).shape == (0,)


@pytest.mark.parametrize(
    ("context", "taper", "start", "end", "message"),
    [
        (-1, 0, 1.0, 0.0, "context_frames"),
        (4, -1, 1.0, 0.0, "taper_frames"),
        (4, 5, 1.0, 0.0, "taper_frames"),
        (4, 2, -0.1, 0.0, "start_strength"),
        (4, 2, 1.1, 0.0, "start_strength"),
        (4, 2, 1.0, -0.1, "end_strength"),
        (4, 2, 1.0, 1.1, "end_strength"),
    ],
)
def test_linear_context_strength_rejects_invalid_values(
    context, taper, start, end, message
):
    dance = load_dance_module()

    with pytest.raises(ValueError, match=message):
        dance.build_linear_context_strength(context, taper, start, end)


def test_rgb_strength_converts_to_latent_mask_without_one_to_one_assumption():
    dance = load_dance_module()
    strength = dance.build_linear_context_strength(24, 12, 1.0, 0.0)

    noise_mask = dance.context_strength_to_latent_mask(strength, latent_ticks=7)

    assert noise_mask.shape == (7,)
    assert noise_mask[0].item() == pytest.approx(0.0)
    assert noise_mask[-1].item() == pytest.approx(1.0)
    assert torch.all(noise_mask[1:] >= noise_mask[:-1])


def test_constant_continuity_strength_maps_to_constant_noise_mask():
    dance = load_dance_module()
    strength = dance.build_linear_context_strength(24, 0, 0.8, 0.0)

    noise_mask = dance.context_strength_to_latent_mask(strength, latent_ticks=7)

    assert torch.allclose(noise_mask, torch.full((7,), 0.2))


@pytest.mark.parametrize("latent_ticks", [-1, 0])
def test_nonempty_rgb_strength_requires_positive_latent_ticks(latent_ticks):
    dance = load_dance_module()

    with pytest.raises(ValueError, match="latent_ticks"):
        dance.context_strength_to_latent_mask(torch.ones(24), latent_ticks)
