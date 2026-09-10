from __future__ import annotations

import json
import os
from pathlib import Path


PROJECT_ROOT = Path(
    os.environ.get("DANCE_PROJECT_ROOT", Path(__file__).resolve().parents[1])
)
WORKFLOW = PROJECT_ROOT / "example_workflows" / "H3_DanceTransfer_AB_Test.json"


def load_workflow():
    return json.loads(WORKFLOW.read_text(encoding="utf-8"))


def test_dance_benchmark_is_a_connected_long_reference_workflow():
    workflow = load_workflow()
    node_types = {node["type"] for node in workflow["nodes"]}

    assert {
        "MiniMaxH3TimelinePlanner",
        "MiniMaxH3LongReferenceSegmentPlan",
        "MiniMaxH3FiniteSegmentSampler",
        "CreateVideo",
        "SaveVideo",
    } <= node_types
    assert len(workflow["links"]) == workflow["last_link_id"]


def test_dance_benchmark_exposes_single_variable_ab_controls_without_pose_depth():
    workflow = load_workflow()
    planner = next(
        node for node in workflow["nodes"]
        if node["type"] == "MiniMaxH3TimelinePlanner"
    )
    timeline = json.loads(planner["widgets_values_named"]["timeline_data"])
    continuation = timeline["danceContinuation"]

    assert timeline["videoClips"][0]["referenceMode"] in {"edit", "guide"}
    assert timeline["videoClips"][0]["file"] == "dance_source.mp4"
    assert len(timeline["images"]) == 2
    assert continuation == {
        "enabled": True,
        "contextFrames": 24,
        "taperEnabled": True,
        "taperFrames": 12,
        "startStrength": 1,
        "endStrength": 0,
        "contextNoiseEnabled": False,
        "contextNoiseStrength": 0,
        "contextNoiseTaperFrames": 4,
    }
    assert not any(
        "dwpose" in node["type"].lower() or "depth" in node["type"].lower()
        for node in workflow["nodes"]
    )
    assert not any("depth" in key.lower() or "dwpose" in key.lower() for key in timeline)
