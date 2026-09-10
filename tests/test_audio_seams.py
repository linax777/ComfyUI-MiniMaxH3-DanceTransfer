from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest
import torch


PROJECT_ROOT = Path(
    os.environ.get("DANCE_PROJECT_ROOT", Path(__file__).resolve().parents[1])
)
MODULE_PATH = PROJECT_ROOT / "audio_seams.py"


def load_audio_seams():
    spec = importlib.util.spec_from_file_location("audio_seams", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_audio_ticks_follow_exact_audio_clock_independent_of_video_alignment():
    seams = load_audio_seams()

    assert seams.audio_ticks_for_rgb_frames(22) == 37
    assert seams.audio_ticks_for_rgb_frames(24) == 40
    assert seams.audio_ticks_for_rgb_frames(39) == 65


def test_equal_power_crossfade_replaces_hard_jump_without_changing_timeline_length():
    seams = load_audio_seams()
    left = torch.tensor([[[1.0] * 8, [0.5] * 8]], dtype=torch.float32)
    right = torch.tensor([[[-1.0] * 8, [-0.5] * 8]], dtype=torch.float32)

    joined = seams.equal_power_crossfade(left, right, overlap_samples=4)

    assert joined.shape == (1, 2, 12)
    assert torch.equal(joined[..., :4], left[..., :4])
    assert torch.equal(joined[..., -4:], right[..., -4:])
    assert joined[0, 0, 4].item() == pytest.approx(1.0)
    assert joined[0, 0, 7].item() == pytest.approx(-1.0)
    assert torch.max(torch.abs(torch.diff(joined[0, 0]))).item() < 1.0


def test_equal_power_crossfade_does_not_raise_correlated_stereo_peaks():
    seams = load_audio_seams()
    left = torch.tensor(
        [[[0.25] * 8, [0.75] * 8]], dtype=torch.float32,
    )
    right = left.clone()

    joined = seams.equal_power_crossfade(left, right, overlap_samples=6)

    expected = torch.tensor(
        [[[0.25] * 10, [0.75] * 10]], dtype=torch.float32,
    )
    assert joined.shape == (1, 2, 10)
    assert torch.allclose(joined, expected)
    assert torch.max(torch.abs(joined)).item() <= 0.75 + 1e-6
    assert torch.allclose(joined[0, 0], torch.full((10,), 0.25))
    assert torch.allclose(joined[0, 1], torch.full((10,), 0.75))


def test_equal_power_crossfade_rejects_incompatible_audio_shapes():
    seams = load_audio_seams()
    left = torch.zeros((1, 2, 8), dtype=torch.float32)
    right = torch.zeros((1, 1, 8), dtype=torch.float32)

    with pytest.raises(ValueError, match="batch and channel dimensions"):
        seams.equal_power_crossfade(left, right, overlap_samples=4)


def test_zero_overlap_is_a_plain_concatenation():
    seams = load_audio_seams()
    left = torch.tensor([[[1.0, 2.0]]], dtype=torch.float32)
    right = torch.tensor([[[3.0, 4.0]]], dtype=torch.float32)

    joined = seams.equal_power_crossfade(left, right, overlap_samples=0)

    assert joined.tolist() == [[[1.0, 2.0, 3.0, 4.0]]]


def main():
    test_audio_ticks_follow_exact_audio_clock_independent_of_video_alignment()
    test_equal_power_crossfade_replaces_hard_jump_without_changing_timeline_length()
    test_equal_power_crossfade_does_not_raise_correlated_stereo_peaks()
    test_equal_power_crossfade_rejects_incompatible_audio_shapes()
    test_zero_overlap_is_a_plain_concatenation()
    print("audio seam tests: PASS")


if __name__ == "__main__":
    main()
