# Dance Transfer Baseline

Upstream repository:
Songssx/ComfyUI-MiniMaxH3-TimelineDirector

Baseline commit:
e4d6d5e

Primary use case:
single-person dance/performance transfer with character and background replacement.

Known empirical observations:
- RGB source video performs at least as well as Depth for motion transfer.
- Depth can lose subtle 3D/body articulation and cause H3 to guess motion.
- approximately 24 RGB frames of overlap gives good segment continuity.
- motion fidelity is more important than maximum clip duration.
