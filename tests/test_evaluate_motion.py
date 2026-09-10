from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(
    os.environ.get("DANCE_PROJECT_ROOT", Path(__file__).resolve().parents[1])
)
MODULE_PATH = PROJECT_ROOT / "tools" / "evaluate_motion.py"


def load_module():
    spec = importlib.util.spec_from_file_location("evaluate_motion", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sequence(xs):
    return {
        "fps": 24,
        "width": 100,
        "height": 200,
        "frames": [
            {
                "left_wrist": [x, 100],
                "right_wrist": [100 - x, 100],
                "hip_center": [50, 120],
            }
            for x in xs
        ],
    }


def test_identical_motion_has_zero_error():
    metrics = load_module().evaluate(sequence([10, 20, 35, 55]), sequence([10, 20, 35, 55]))

    assert metrics["mean_joint_error"] == 0.0
    assert metrics["acceleration_error"] == 0.0
    assert metrics["missing_keypoint_rate"]["source"] == 0.0
    assert metrics["missing_keypoint_rate"]["generated"] == 0.0
    assert metrics["trajectory_timing_offset_frames"] == 0


def test_timing_search_detects_one_frame_delay():
    source = sequence([10, 20, 30, 40, 50])
    generated = sequence([0, 10, 20, 30, 40, 50])

    metrics = load_module().evaluate(source, generated, max_offset_frames=2)

    assert metrics["trajectory_timing_offset_frames"] == 1
    assert metrics["timing_aligned_joint_error"] == 0.0


def test_missing_keypoints_are_reported_without_crashing():
    source = sequence([10, 20, 30])
    generated = sequence([10, 20, 30])
    generated["frames"][1].pop("left_wrist")

    metrics = load_module().evaluate(source, generated)

    assert metrics["missing_keypoint_rate"]["generated"] > 0
    assert metrics["matched_observations"] == 8
