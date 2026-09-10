# MiniMax H3 Dance Node Namespace Migration

MiniMax H3 Dance Transfer uses a plugin-owned node namespace so it can be
installed alongside the upstream MiniMax H3 Timeline Director without node-ID
collisions. This is a breaking change for dance workflows saved before the
rename.

## Update saved workflows

Open each pre-rename dance workflow and replace every node type with the
corresponding new type below. Depending on the workflow format, the node type
is stored in a `type` or `class_type` field.

| Old node type | New node type |
| --- | --- |
| `MiniMaxH3TimelineDirector` | `MiniMaxH3DanceTimelineDirector` |
| `MiniMaxH3TimelinePlanner` | `MiniMaxH3DanceTimelinePlanner` |
| `MiniMaxH3TimelineEncoder` | `MiniMaxH3DanceTimelineEncoder` |
| `MiniMaxH3OmniPromptBridge` | `MiniMaxH3DanceOmniPromptBridge` |
| `MiniMaxH3AddLatentGuide` | `MiniMaxH3DanceAddLatentGuide` |
| `MiniMaxH3VisualDifferenceMetrics` | `MiniMaxH3DanceVisualDifferenceMetrics` |
| `MiniMaxH3FiniteSegmentExpansion` | `MiniMaxH3DanceFiniteSegmentExpansion` |
| `MiniMaxH3LongReferenceSegmentPlan` | `MiniMaxH3DanceLongReferenceSegmentPlan` |
| `MiniMaxH3FiniteSegmentSampler` | `MiniMaxH3DanceFiniteSegmentSampler` |
| `MiniMaxH3FiniteAudioTrimTail` | `MiniMaxH3DanceFiniteAudioTrimTail` |
| `MiniMaxH3FiniteOutputTrim` | `MiniMaxH3DanceFiniteOutputTrim` |
| `MiniMaxH3FiniteLatentContinuation` | `MiniMaxH3DanceFiniteLatentContinuation` |
| `MiniMaxH3FiniteSegmentFinalize` | `MiniMaxH3DanceFiniteSegmentFinalize` |

No old node aliases are registered. A workflow that still contains an old
node type will resolve to the upstream node when it is installed, or fail to
load when it is not.

Ordinary widget values and `timeline_data` require no conversion. Replace only
the node types listed above, then reconnect only if ComfyUI reports a missing
connection after loading the workflow.
