from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re


PROJECT_ROOT = Path(
    os.environ.get("DANCE_PROJECT_ROOT", Path(__file__).resolve().parents[1])
)
MODULE_PATH = PROJECT_ROOT / "dance_namespace.py"
RUNTIME_PATHS = {
    "registration": PROJECT_ROOT / "__init__.py",
    "timeline": PROJECT_ROOT / "minimax_h3_timeline_director.py",
    "finite_segments": PROJECT_ROOT / "minimax_h3_finite_segments.py",
    "latent_guide": PROJECT_ROOT / "experimental_latent_guide.py",
}
JAVASCRIPT_PATH = PROJECT_ROOT / "js" / "minimax_h3_timeline_director.js"
LOCALE_PATHS = {
    "en_main": PROJECT_ROOT / "locales" / "en" / "main.json",
    "en_node_defs": PROJECT_ROOT / "locales" / "en" / "nodeDefs.json",
    "zh_main": PROJECT_ROOT / "locales" / "zh" / "main.json",
    "zh_node_defs": PROJECT_ROOT / "locales" / "zh" / "nodeDefs.json",
}
WORKFLOW_PATHS = tuple((PROJECT_ROOT / "example_workflows").glob("*.json")) + (
    PROJECT_ROOT / "tests" / "experiments" / "minimax_h3_latent_guide_ab_api.json",
)

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


def collect_node_ids(value):
    """Collect serialized ComfyUI node identities from a JSON artifact."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"type", "class_type"}:
                yield child
            yield from collect_node_ids(child)
    elif isinstance(value, list):
        for child in value:
            yield from collect_node_ids(child)


def collect_aux_ids(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "aux_id":
                yield child
            yield from collect_aux_ids(child)
    elif isinstance(value, list):
        for child in value:
            yield from collect_aux_ids(child)


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


def test_runtime_sources_expose_only_dance_owned_node_ids():
    """Catch an upstream-ID registration that would collide at ComfyUI load time."""
    namespace = load_namespace()
    sources = {
        name: path.read_text(encoding="utf-8") for name, path in RUNTIME_PATHS.items()
    }

    for source in sources.values():
        for old_node_id in namespace.UPSTREAM_OWNED_NODE_IDS:
            assert f'"{old_node_id}"' not in source

    registration_source = sources["registration"]
    for node_key in EXPECTED:
        assert f'DANCE_NODE_IDS["{node_key}"]' in registration_source
    for old_node_id in namespace.UPSTREAM_OWNED_NODE_IDS:
        assert old_node_id not in registration_source

    timeline_source = sources["timeline"]
    assert '"MiniMaxH3AddGuide"' in timeline_source
    assert "MiniMaxH3SigmaShift" not in namespace.UPSTREAM_OWNED_NODE_IDS


def test_frontend_locales_and_serialized_artifacts_use_dance_node_namespace():
    """Catch artifacts that would resolve to an upstream node instead of this plugin."""
    namespace = load_namespace()
    javascript = JAVASCRIPT_PATH.read_text(encoding="utf-8")
    locales = {
        name: json.loads(path.read_text(encoding="utf-8"))
        for name, path in LOCALE_PATHS.items()
    }

    assert "MiniMaxH3DanceTimelinePlanner" in javascript
    assert "MiniMaxH3TimelinePlanner" not in javascript
    assert set(locales["en_node_defs"]) == set(locales["zh_node_defs"]) == set(
        namespace.DANCE_NODE_IDS.values()
    )
    assert "MiniMaxH3DanceTimelineDirector" in locales["en_main"]
    assert "MiniMaxH3DanceTimelineDirector" in locales["zh_main"]
    for node_defs in (locales["en_node_defs"], locales["zh_node_defs"]):
        assert all(
            definition["display_name"].startswith("MiniMax H3 Dance")
            for definition in node_defs.values()
        )

    artifact_node_ids = set()
    artifact_aux_ids = set()
    for path in WORKFLOW_PATHS:
        artifact = json.loads(path.read_text(encoding="utf-8"))
        artifact_node_ids.update(collect_node_ids(artifact))
        artifact_aux_ids.update(collect_aux_ids(artifact))

    assert artifact_node_ids.isdisjoint(namespace.UPSTREAM_OWNED_NODE_IDS)
    assert "MiniMaxH3AddGuide" in artifact_node_ids
    assert artifact_aux_ids == {"linax777/ComfyUI-MiniMaxH3-DanceTransfer"}


def test_frontend_registers_a_dance_specific_extension_name():
    """Catch a ComfyUI frontend hook registration collision with upstream."""
    javascript = JAVASCRIPT_PATH.read_text(encoding="utf-8")
    registration = re.search(
        r'app\.registerExtension\(\{\s*name:\s*"([^"]+)"', javascript
    )

    assert registration is not None
    assert registration.group(1) == "MiniMaxH3Dance.TimelineDirector"
    assert registration.group(1) != "MiniMaxH3.TimelineDirector"
