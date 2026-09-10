from types import MappingProxyType


DANCE_NODE_IDS = MappingProxyType(
    {
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
)

DANCE_CATEGORIES = MappingProxyType(
    {
        "root": "MiniMax H3 Dance",
        "long_video": "MiniMax H3 Dance/Long Video",
        "experimental": "MiniMax H3 Dance/Experimental",
        "internal": "MiniMax H3 Dance/Internal",
    }
)

UPSTREAM_OWNED_NODE_IDS = frozenset(
    {
        "MiniMaxH3TimelineDirector",
        "MiniMaxH3TimelinePlanner",
        "MiniMaxH3TimelineEncoder",
        "MiniMaxH3OmniPromptBridge",
        "MiniMaxH3AddLatentGuide",
        "MiniMaxH3VisualDifferenceMetrics",
        "MiniMaxH3FiniteSegmentExpansion",
        "MiniMaxH3LongReferenceSegmentPlan",
        "MiniMaxH3FiniteSegmentSampler",
        "MiniMaxH3FiniteAudioTrimTail",
        "MiniMaxH3FiniteOutputTrim",
        "MiniMaxH3FiniteLatentContinuation",
        "MiniMaxH3FiniteSegmentFinalize",
    }
)
