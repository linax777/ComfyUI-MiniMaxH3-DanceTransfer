#!/usr/bin/env python3
"""Compare source/generated 2D keypoint JSON without adding runtime dependencies.

Input files contain ``width``, ``height``, optional ``fps``, and a ``frames``
list. Each frame maps a joint name to ``[x, y]`` or ``[x, y, confidence]``.
This tool is deliberately separate from ComfyUI startup and performs no pose
extraction; any extractor may produce the JSON inputs.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


TARGET_JOINTS = (
    "left_wrist",
    "right_wrist",
    "left_ankle",
    "right_ankle",
    "hip_center",
    "shoulder_center",
    "body_bbox_center",
)


def _validate(sequence: dict[str, Any], label: str) -> None:
    if not isinstance(sequence, dict):
        raise ValueError(f"{label} must be a JSON object")
    if float(sequence.get("width") or 0) <= 0 or float(sequence.get("height") or 0) <= 0:
        raise ValueError(f"{label} width and height must be positive")
    if not isinstance(sequence.get("frames"), list):
        raise ValueError(f"{label} frames must be a list")


def _joint_names(source: dict[str, Any], generated: dict[str, Any]) -> tuple[str, ...]:
    present = {
        name
        for sequence in (source, generated)
        for frame in sequence["frames"]
        if isinstance(frame, dict)
        for name in frame
    }
    preferred = tuple(name for name in TARGET_JOINTS if name in present)
    extras = tuple(sorted(present.difference(preferred)))
    return preferred + extras


def _point(sequence: dict[str, Any], frame_index: int, joint: str):
    frames = sequence["frames"]
    if not 0 <= frame_index < len(frames) or not isinstance(frames[frame_index], dict):
        return None
    value = frames[frame_index].get(joint)
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        return None
    try:
        x, y = float(value[0]), float(value[1])
        confidence = float(value[2]) if len(value) > 2 else 1.0
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(item) for item in (x, y, confidence)) or confidence <= 0:
        return None
    return x / float(sequence["width"]), y / float(sequence["height"])


def _mean_joint_error(source, generated, joints, offset):
    distances = []
    for source_index in range(len(source["frames"])):
        generated_index = source_index + offset
        for joint in joints:
            source_point = _point(source, source_index, joint)
            generated_point = _point(generated, generated_index, joint)
            if source_point is not None and generated_point is not None:
                distances.append(math.dist(source_point, generated_point))
    return (sum(distances) / len(distances) if distances else None), len(distances)


def _acceleration_error(source, generated, joints):
    errors = []
    common_frames = min(len(source["frames"]), len(generated["frames"]))
    for index in range(1, common_frames - 1):
        for joint in joints:
            source_points = [_point(source, item, joint) for item in (index - 1, index, index + 1)]
            generated_points = [_point(generated, item, joint) for item in (index - 1, index, index + 1)]
            if None in source_points or None in generated_points:
                continue
            source_acceleration = tuple(
                source_points[2][axis] - 2 * source_points[1][axis] + source_points[0][axis]
                for axis in (0, 1)
            )
            generated_acceleration = tuple(
                generated_points[2][axis] - 2 * generated_points[1][axis] + generated_points[0][axis]
                for axis in (0, 1)
            )
            errors.append(math.dist(source_acceleration, generated_acceleration))
    return sum(errors) / len(errors) if errors else 0.0


def _missing_rate(sequence, joints):
    total = len(sequence["frames"]) * len(joints)
    if total == 0:
        return 0.0
    missing = sum(
        _point(sequence, index, joint) is None
        for index in range(len(sequence["frames"]))
        for joint in joints
    )
    return missing / total


def evaluate(source, generated, max_offset_frames=24):
    """Return normalized motion, acceleration, missingness, and timing metrics."""

    _validate(source, "source")
    _validate(generated, "generated")
    joints = _joint_names(source, generated)
    if not joints:
        raise ValueError("No keypoint names were found")

    mean_error, matched = _mean_joint_error(source, generated, joints, 0)
    candidates = []
    limit = max(0, int(max_offset_frames))
    for offset in range(-limit, limit + 1):
        error, count = _mean_joint_error(source, generated, joints, offset)
        if error is not None:
            candidates.append((error, -count, abs(offset), offset))
    if not candidates or mean_error is None:
        raise ValueError("Source and generated sequences have no matching keypoints")
    aligned_error, _, _, best_offset = min(candidates)

    return {
        "joints": list(joints),
        "source_frames": len(source["frames"]),
        "generated_frames": len(generated["frames"]),
        "matched_observations": matched,
        "mean_joint_error": mean_error,
        "acceleration_error": _acceleration_error(source, generated, joints),
        "missing_keypoint_rate": {
            "source": _missing_rate(source, joints),
            "generated": _missing_rate(generated, joints),
        },
        "trajectory_timing_offset_frames": best_offset,
        "trajectory_timing_offset_seconds": best_offset / float(source.get("fps") or 24),
        "timing_aligned_joint_error": aligned_error,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Source keypoint JSON")
    parser.add_argument("generated", type=Path, help="Generated keypoint JSON")
    parser.add_argument("--max-offset-frames", type=int, default=24)
    parser.add_argument("--output", type=Path, help="Optional report JSON path")
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    generated = json.loads(args.generated.read_text(encoding="utf-8"))
    report = evaluate(source, generated, args.max_offset_frames)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
