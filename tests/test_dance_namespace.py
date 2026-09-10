from __future__ import annotations

import importlib.util
import os
from pathlib import Path


PROJECT_ROOT = Path(
    os.environ.get("DANCE_PROJECT_ROOT", Path(__file__).resolve().parents[1])
)
MODULE_PATH = PROJECT_ROOT / "dance_namespace.py"

EXPECTED = {
    "timeline_director": "MiniMaxH3DanceTimelineDirector",
    "timeline_planner": "MiniMaxH3DanceTimelinePlanner",
    "timeline_encoder": "MiniMaxH3DanceTimelineEncoder",
    "omni_prompt_bridge": "MiniMaxH3DanceOmniPromptBridge",
    "add_latent_guide": "MiniMaxH3DanceAddLatentGuide",
    "visual_difference_metrics": "MiniMaxH3DanceVisualDifferenceMetrics",
    "finite_segment_expansion": "MiniMaxH3DanceFiniteSegmentExpansion",
    "long_reference_segment_plan": "MiniMaxH3DanceLongReferenceSegmentPlan",
    "finite_segment_sampler": "MiniMaxH3DanceFiniteSegmentSampler",
    "finite_audio_trim_tail": "MiniMaxH3DanceFiniteAudioTrimTail",
    "finite_output_trim": "MiniMaxH3DanceFiniteOutputTrim",
    "finite_latent_continuation": "MiniMaxH3DanceFiniteLatentContinuation",
    "finite_segment_finalize": "MiniMaxH3DanceFiniteSegmentFinalize",
}


def load_namespace():
    spec = importlib.util.spec_from_file_location("dance_namespace", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_dance_node_ids_are_collision_free_and_exact():
    namespace = load_namespace()

    assert namespace.DANCE_NODE_IDS == EXPECTED
    assert set(EXPECTED.values()).isdisjoint(namespace.UPSTREAM_OWNED_NODE_IDS)
    assert all(value.startswith("MiniMaxH3Dance") for value in EXPECTED.values())


def test_dance_categories_are_exact():
    namespace = load_namespace()

    assert namespace.DANCE_CATEGORIES == {
        "root": "MiniMax H3 Dance",
        "long_video": "MiniMax H3 Dance/Long Video",
        "experimental": "MiniMax H3 Dance/Experimental",
        "internal": "MiniMax H3 Dance/Internal",
    }
