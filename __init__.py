"""MiniMax H3 Dance Timeline Director for ComfyUI."""

from .dance_namespace import DANCE_NODE_IDS

from .minimax_h3_timeline_director import (
    MiniMaxH3DanceTimelineDirector,
    MiniMaxH3DanceTimelineEncoder,
    MiniMaxH3DanceOmniPromptBridge,
    MiniMaxH3DanceTimelinePlanner,
)
from .experimental_latent_guide import (
    MiniMaxH3DanceAddLatentGuide,
    MiniMaxH3DanceVisualDifferenceMetrics,
)
from .minimax_h3_finite_segments import (
    MiniMaxH3DanceLongReferenceSegmentPlan,
    MiniMaxH3DanceFiniteLatentContinuation,
    MiniMaxH3DanceFiniteSegmentExpansion,
    MiniMaxH3DanceFiniteAudioTrimTail,
    MiniMaxH3DanceFiniteOutputTrim,
    MiniMaxH3DanceFiniteSegmentFinalize,
    MiniMaxH3DanceFiniteSegmentSampler,
)

NODE_CLASS_MAPPINGS = {
    DANCE_NODE_IDS["timeline_director"]: MiniMaxH3DanceTimelineDirector,
    DANCE_NODE_IDS["timeline_planner"]: MiniMaxH3DanceTimelinePlanner,
    DANCE_NODE_IDS["timeline_encoder"]: MiniMaxH3DanceTimelineEncoder,
    DANCE_NODE_IDS["omni_prompt_bridge"]: MiniMaxH3DanceOmniPromptBridge,
    DANCE_NODE_IDS["add_latent_guide"]: MiniMaxH3DanceAddLatentGuide,
    DANCE_NODE_IDS["visual_difference_metrics"]: MiniMaxH3DanceVisualDifferenceMetrics,
    DANCE_NODE_IDS["finite_segment_expansion"]: MiniMaxH3DanceFiniteSegmentExpansion,
    DANCE_NODE_IDS["long_reference_segment_plan"]: MiniMaxH3DanceLongReferenceSegmentPlan,
    DANCE_NODE_IDS["finite_segment_sampler"]: MiniMaxH3DanceFiniteSegmentSampler,
    DANCE_NODE_IDS["finite_audio_trim_tail"]: MiniMaxH3DanceFiniteAudioTrimTail,
    DANCE_NODE_IDS["finite_output_trim"]: MiniMaxH3DanceFiniteOutputTrim,
    DANCE_NODE_IDS["finite_latent_continuation"]: MiniMaxH3DanceFiniteLatentContinuation,
    DANCE_NODE_IDS["finite_segment_finalize"]: MiniMaxH3DanceFiniteSegmentFinalize,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    DANCE_NODE_IDS["timeline_director"]: "MiniMax H3 Dance Timeline Director",
    DANCE_NODE_IDS["timeline_planner"]: "MiniMax H3 Dance Material Planner",
    DANCE_NODE_IDS["timeline_encoder"]: "MiniMax H3 Dance Plan Encoder",
    DANCE_NODE_IDS["omni_prompt_bridge"]: "MiniMax H3 Dance Omni Media Prompt Bridge",
    DANCE_NODE_IDS["add_latent_guide"]: "MiniMax H3 Dance Direct Latent Guide (Experimental)",
    DANCE_NODE_IDS["visual_difference_metrics"]: "MiniMax H3 Dance Video Difference Metrics (Experimental)",
    DANCE_NODE_IDS["finite_segment_expansion"]: "MiniMax H3 Dance Finite Segment Expansion",
    DANCE_NODE_IDS["long_reference_segment_plan"]: "MiniMax H3 Dance Long Reference Auto Segmentation",
    DANCE_NODE_IDS["finite_segment_sampler"]: "MiniMax H3 Dance Finite Segment Sampler",
    DANCE_NODE_IDS["finite_audio_trim_tail"]: "MiniMax H3 Dance Finite Audio Tail Trim (Internal)",
    DANCE_NODE_IDS["finite_output_trim"]: "MiniMax H3 Dance Finite Output Trim (Internal)",
    DANCE_NODE_IDS["finite_latent_continuation"]: "MiniMax H3 Dance Finite Latent Continuation (Internal)",
    DANCE_NODE_IDS["finite_segment_finalize"]: "MiniMax H3 Dance Finite Segment Finalize (Internal)",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
