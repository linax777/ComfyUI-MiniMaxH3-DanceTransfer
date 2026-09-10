# Dance Conditioning Architecture

## Baseline

This branch starts at `Songssx/ComfyUI-MiniMaxH3-TimelineDirector@e4d6d5e`.
Dance continuation is additive and disabled by default. Source RGB and generated
continuity context are deliberately kept as separate inputs until immediately
before H3 sampling.

## Source-motion path

1. `minimax_h3_timeline_director._create_timeline_plan` parses the serialized
   timeline and creates the lightweight material plan. `_video_reference_specs`
   resolves every selected clip to an exact file, source start, duration, and
   selected `referenceMode`.
2. `minimax_h3_finite_segments._prepare_long_reference_plan` creates a separate
   timeline plan for every source window. It updates the clip's `trimStart` and
   `duration` but preserves its `referenceMode`.
3. `minimax_h3_timeline_director._build_references` calls `_decode_video` for
   the exact source interval. Editable Reference frames become `ref_video_N`;
   Fixed Guide frames are accumulated in the dedicated `guides` list. Boundary
   Only continues to create only its existing boundary guides.
4. `_encode_timeline_plan` calls `_execute_h3_independent_first`, where
   `comfy.ldm.minimax.nodes._empty_av_latent` creates the target H3 AV latent
   and source RGB references are VAE-encoded as H3 reference blocks.
5. `_apply_h3_guides` constructs Fixed Guides by calling the native
   `MiniMaxH3AddGuide.execute` implementation. No dance setting changes the
   clip's selected source role.

## Continuity-context path

1. `MiniMaxH3FiniteSegmentSampler.execute` retains `sampled.out(0)` under the
   explicit graph role `previous_latent` after each segment finishes.
2. The next segment's independent source-motion plan is encoded first by
   `MiniMaxH3TimelineEncoder`.
3. `MiniMaxH3FiniteLatentContinuation.execute` receives the new target latent
   and the previous clean sampled latent as separate arguments.
4. `experimental_latent_guide._apply_linear_temporal_noise_mask` clones the
   previous latent tail into a disposable target-latent working copy and builds
   the continuation-only noise mask. It never modifies the previous sampled
   latent or any decoded source RGB tensor.

## Point immediately before sampling

`MiniMaxH3FiniteSegmentSampler.execute` connects the two paths as follows:

```text
source RGB interval -> MiniMaxH3TimelineEncoder -> target latent ---------+
                                                                       |
previous clean sampled latent -> MiniMaxH3FiniteLatentContinuation -----+
                                                                       v
                                                   SamplerCustomAdvanced
```

The continuation node returns a masked target latent and a model patched for
that prefix. `BasicGuider` receives the encoder conditioning; then
`SamplerCustomAdvanced` receives both the guider and the continuation result.
The previous tail never replaces the next segment's `source_plan`, source clip,
`trimStart`, reference media, or `referenceMode`.

## Naming contract

- `source_motion_*` means original RGB media for choreography, timing, body
  trajectory, and camera motion.
- `previous_clean_output` means the completed prior result retained for output
  and for deriving the next context.
- `continuity_context_*` or `continuity_working_copy` means disposable data
  derived from that clean result for identity, clothing, background, lighting,
  and seam continuity.

Ambiguous names such as `video`, `guide`, `previous`, and `context` should not
cross these role boundaries without a qualifying prefix.
