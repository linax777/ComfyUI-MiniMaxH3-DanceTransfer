# Dance Transfer Testing

Use `example_workflows/H3_DanceTransfer_AB_Test.json` as the fixed benchmark.
Replace its placeholder source dance video and character image before running.
The optional second picture may define a target background. Keep the seed,
prompt, sampler, model, resolution, source clip, and segment duration identical
between comparisons.

## First A/B matrix

| Test | Continuation | Context | Taper | Experimental noise |
| --- | --- | ---: | --- | --- |
| A | Off (e4d6d5e-compatible) | — | Off | Off |
| B | On | 24 RGB frames | Off | Off |
| C | On | 24 RGB frames | 12-frame linear | Off |
| D | On | 24 RGB frames | 12-frame linear | On, selected strength |

Run each row first with Editable Reference and then with Fixed Guide. Change
only `referenceMode` for that pair. Editable Reference prioritizes replacement
freedom; Fixed Guide prioritizes source motion adherence.

## Context sweep

Test `12, 18, 22, 24, 30, 36` RGB frames while holding every other setting
constant. The report must retain the exact requested RGB value and separately
show its H3-aligned latent tick count.

## Visual acceptance checklist

Use three short sources before any 60-second run:

1. Medium-speed, front-facing dance.
2. Fast arm and leg choreography.
3. Rotation, body occlusion, or turn-around.

Start with 6–10 second segments. Inspect arm trajectory, hand height and side,
leg crossing, foot placement, hip and torso rotation, turning direction,
jump/crouch timing, occlusion recovery, camera movement, identity, background
continuity, seams, and accumulated sharpness.

A candidate passes only when motion is not materially worse than the baseline,
the seam improves or remains equal, identity/background stability improves,
and later segments continue following the original source choreography.

## Optional keypoint metrics

Pose extraction remains external and optional. Export source and generated
keypoints to JSON, then run:

```bash
python tools/evaluate_motion.py source_keypoints.json generated_keypoints.json \
  --output motion_report.json
```

Each JSON object needs `width`, `height`, optional `fps`, and a `frames` array.
Each frame maps names such as `left_wrist`, `right_wrist`, `left_ankle`,
`right_ankle`, `hip_center`, `shoulder_center`, and `body_bbox_center` to
`[x, y]` or `[x, y, confidence]`. The report normalizes image coordinates and
contains mean joint error, acceleration error, missing-keypoint rates, and the
best trajectory timing offset. This evaluator is never imported by ComfyUI.

## VRAM profile record

No production-resolution VRAM figures are recorded yet because this repository
does not include H3 weights or benchmark media. On the target ComfyUI machine,
record peak VRAM for 2 and 4 segments using the same seed and settings:

| Resolution | Segments | Continuation | Peak VRAM | Notes |
| --- | ---: | --- | ---: | --- |
| TBD | 2 | Off | TBD | |
| TBD | 2 | 24f | TBD | |
| TBD | 4 | Off | TBD | |
| TBD | 4 | 24f | TBD | |

The expected live GPU set is the current sampler inputs and output. Finished
assembly and debug metadata should not retain additional source RGB or modified
continuation copies beyond the current segment.

Implementation audit: the target latent is cloned once to become the masked
continuation working copy. With experimental noise off (the default), the clean
source tail is copied directly into that target clone without an intermediate
tail clone. With noise on, exactly one disposable tail clone is modified in
place; `previous_clean_output` remains read-only and is released after its next
segment consumer completes. Actual peak VRAM still requires the production
model, media, resolution, and ComfyUI allocator telemetry listed above.
