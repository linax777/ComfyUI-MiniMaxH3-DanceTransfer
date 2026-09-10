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
FORK_DOCUMENTATION_PATHS = (
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "README_CN.md",
    PROJECT_ROOT / "docs" / "FINITE_SEGMENT_EXPANSION_CN.md",
    PROJECT_ROOT / "docs" / "LONG_REFERENCE_AUTO_SEGMENT_CN.md",
    PROJECT_ROOT / "docs" / "AGENT_LONG_VIDEO_GUIDE_CN.md",
    PROJECT_ROOT / "tests" / "experiments" / "README_CN.md",
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


def test_fork_metadata_and_install_instructions_identify_dance_transfer():
    """Catch package metadata or install instructions that still identify upstream."""
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert 'name = "comfyui-minimax-h3-dance-transfer"' in pyproject
    assert 'DisplayName = "MiniMax H3 Dance Transfer"' in pyproject
    assert "github.com/linax777/ComfyUI-MiniMaxH3-DanceTransfer.git" in readme


def test_fork_documentation_uses_dance_node_names_and_ids():
    """Catch fork documentation that directs users to retired node names or IDs."""
    sources = {
        path.relative_to(PROJECT_ROOT).as_posix(): path.read_text(encoding="utf-8")
        for path in FORK_DOCUMENTATION_PATHS
    }
    combined = "\n".join(sources.values())

    retired_display_names = {
        "MiniMax H3 Material Planner",
        "MiniMax H3 Omni Media-Bundle Prompt Bridge",
        "MiniMax H3 Plan Encoder",
        "MiniMax H3 Finite Segment Expansion",
        "MiniMax H3 Long Reference Auto Segmentation",
        "MiniMax H3 Finite Segment Sampling",
        "MiniMax H3 Timeline Director",
        "MiniMax H3 素材规划台",
        "MiniMax H3 Omni 素材包提示词桥",
        "MiniMax H3 规划编码器",
        "MiniMax H3 有限分段展开",
        "MiniMax H3 长参考自动分段",
        "MiniMax H3 有限分段采样",
        "MiniMax H3 时间线导演台",
    }
    assert all(name not in combined for name in retired_display_names)

    readme = sources["README.md"]
    expected_english_display_names = {
        "MiniMax H3 Dance Material Planner",
        "MiniMax H3 Dance Omni Media Prompt Bridge",
        "MiniMax H3 Dance Plan Encoder",
        "MiniMax H3 Dance Finite Segment Expansion",
        "MiniMax H3 Dance Long Reference Auto Segmentation",
        "MiniMax H3 Dance Finite Segment Sampler",
        "MiniMax H3 Dance Timeline Director",
    }
    assert all(name in readme for name in expected_english_display_names)

    chinese_readme = sources["README_CN.md"]
    expected_chinese_display_names = {
        "MiniMax H3 Dance 素材规划台",
        "MiniMax H3 Dance Omni 素材包提示词桥",
        "MiniMax H3 Dance 规划编码器",
        "MiniMax H3 Dance 有限分段展开",
        "MiniMax H3 Dance 长参考自动分段",
        "MiniMax H3 Dance 有限分段采样",
        "MiniMax H3 Dance 时间线导演台",
    }
    assert all(name in chinese_readme for name in expected_chinese_display_names)

    assert "MiniMax H3 Dance 有限分段展开" in sources[
        "docs/FINITE_SEGMENT_EXPANSION_CN.md"
    ]
    assert "MiniMax H3 Dance 长参考自动分段" in sources[
        "docs/LONG_REFERENCE_AUTO_SEGMENT_CN.md"
    ]
    assert "MiniMax H3 Dance 时间线导演台" in sources[
        "docs/AGENT_LONG_VIDEO_GUIDE_CN.md"
    ]

    experiment = sources["tests/experiments/README_CN.md"]
    assert "MiniMaxH3DanceAddLatentGuide" in experiment
    assert "MiniMaxH3DanceVisualDifferenceMetrics" in experiment
    assert "MiniMaxH3AddLatentGuide" not in experiment
    assert "MiniMaxH3VisualDifferenceMetrics" not in experiment


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
