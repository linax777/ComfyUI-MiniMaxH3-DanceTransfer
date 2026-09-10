# ComfyUI MiniMax H3 Dance Transfer — Motion-First Character Replacement

[Traditional Chinese](README_CN.md) · English

Dance and performance transfer nodes for ComfyUI's native **MiniMax H3 Reference to Video** workflow. This fork is designed to preserve the choreography, timing, body motion, and camera language of an original RGB performance while replacing the performer and maintaining identity, clothing, background, and lighting across multiple generated segments.

## Project goal

The project separates two conditioning responsibilities that should not compete with each other:

```text
Original dance RGB segment ──> choreography, timing, pose, and camera motion
Previous generated tail  ──> identity, clothing, background, lighting, and seam continuity
```

The original source interval always remains the primary motion reference. Previous generated context stabilizes the beginning of the next segment and can taper away so it does not replace or override the source choreography.

The default requested continuation context is **24 RGB frames at 24 fps**. It is aligned to MiniMax H3's legal temporal grid during execution. Version 1 deliberately stays RGB-first and does not add Depth or DWPose conditioning.

## What this fork adds

- Motion-first dance and performance transfer with source RGB kept as the authoritative motion guide.
- Separate Dance Continuation controls for generated-tail context, tapering, strength, and optional experimental noise.
- Direct AV-latent continuation without an RGB decode/re-encode round trip between segments.
- Adaptive Drift-Control masking that preserves the seam-side latent while releasing the disposable prefix.
- Soft AV audio continuation for smoother cross-segment sound transitions.
- Automatic long-reference segmentation for character replacement and long-form lip sync.
- Exact final trimming after H3 temporal-grid alignment and overlap removal.
- A compact timeline for video, paired soundtrack, Guide, image, and standalone audio references.
- A plugin-owned `MiniMaxH3Dance*` namespace that can coexist with the upstream Timeline Director.

## Recommended workflow

1. Load one RGB dance or performance video in **MiniMax H3 Dance Material Planner**.
2. Choose `Editable Reference` when the performer should be replaced. `Fixed Guide` anchors the original pixels and usually prevents character replacement.
3. Add identity images and, when needed, a standalone driving-audio track.
4. Use **MiniMax H3 Dance Long Reference Auto Segmentation** for a complete source performance, or **MiniMax H3 Dance Finite Segment Expansion** for a manually planned long sequence.
5. Connect the plan to **MiniMax H3 Dance Finite Segment Sampler** and enable Dance Continuation when cross-segment identity stability is required.
6. Start with the default 24-frame context, compare against the baseline, and tune tapering only when the generated context begins to resist the source motion.

For controlled comparison, begin with the [Dance Transfer A/B benchmark workflow](example_workflows/H3_DanceTransfer_AB_Test.json).

## Examples

These approximately one-minute examples were generated in one plugin execution. Each output is `52.625 seconds / 1263 frames / 24 fps`. The historical media files remain hosted as upstream GitHub Release assets and do not increase the clone size.

| Direct latent continuation | Reference material with a 48-frame requested overlap |
| --- | --- |
| [![Play direct-latent example](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/case-finite-segments-60s.webp)](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/H3_finite_segments_60s.mp4) | [![Play reference-overlap example](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/case-reference-overlap-60s.webp)](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/H3_reference_overlap48_60s.mp4) |

## Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/linax777/ComfyUI-MiniMaxH3-DanceTransfer.git
```

Restart ComfyUI and search for `MiniMax H3 Dance`.

### Requirements

- A recent ComfyUI build containing the native MiniMax H3 nodes.
- `MiniMaxH3AddGuide` when Fixed Guide conditioning is used.
- A MiniMax H3 Ref2VA model, CLIP, video VAE, and audio VAE.
- Python 3.10 or newer.
- ComfyUI's `imageio-ffmpeg` package for low-resolution preview proxies.

No additional pip dependency is declared. The plugin uses PyAV, Pillow, NumPy, PyTorch, torchaudio, aiohttp, and imageio-ffmpeg normally supplied by a compatible ComfyUI installation.

## Included nodes

| Node | Purpose |
| --- | --- |
| **MiniMax H3 Dance Material Planner** | Edits reference media and produces an H3 plan plus an ordered Omni media bundle. |
| **MiniMax H3 Dance Omni Media Prompt Bridge** | Sends the ordered bundle to an installed Prompt Rewriter Omni backend. |
| **MiniMax H3 Dance Plan Encoder** | Converts the plan, prompt, CLIP, and VAEs into H3 conditioning and latent outputs. |
| **MiniMax H3 Dance Long Reference Auto Segmentation** | Splits one long performance and synchronized audio into source-aligned generation windows. |
| **MiniMax H3 Dance Finite Segment Expansion** | Builds a lightweight finite long-video plan without sampling. |
| **MiniMax H3 Dance Finite Segment Sampler** | Expands the plan into direct-latent continuation, masking, sampling, overlap removal, and assembly. |
| **MiniMax H3 Dance Timeline Director** | Provides the all-in-one timeline planning and encoding interface. |

The split planner path avoids a ComfyUI dependency cycle:

```text
Material Planner ──Omni bundle──> Omni Media Prompt Bridge ──rewritten_prompt──> Plan Encoder
       └──────────────────────── H3 plan ────────────────────────> Plan Encoder
```

## Included workflows

- [Dance Transfer A/B benchmark](example_workflows/H3_DanceTransfer_AB_Test.json): compares the protected RGB baseline with Dance Continuation.
- [Long-video motion transfer, character replacement, and digital-human workflow](example_workflows/MinimaxH3长视频动作迁移人物替换+长视频数字人工作流.json): automatically slices one source performance and optional long audio.
- [Finite direct-latent continuation](example_workflows/MiniMax时间线插件内置有限分段工作流.json): creates a finite acyclic segment graph without generic Loop nodes.
- [Basic timeline workflow](example_workflows/MiniMax_H3基础时间线规划工作流.json): uses the all-in-one Dance Timeline Director.
- [Split planner and encoder](example_workflows/MiniMax_H3时间线规划拆分节点工作流.json): separates media planning from H3 encoding.
- [Planning with prompt expansion](example_workflows/MiniMax_H3时间规划+Prompt提示词生成.json): integrates [MiniMax-H3-Prompt-Rewriter-ComfyUI](https://github.com/pytraveler/MiniMax-H3-Prompt-Rewriter-ComfyUI).

## Dance Continuation guidance

- Treat the original RGB segment and previous generated tail as different inputs with different jobs.
- Do not globally convert source clips to Fixed Guide when Dance Continuation is enabled.
- A requested 24-frame context may become a smaller aligned overlap because MiniMax H3 uses a legal temporal grid; all continuation, trimming, and assembly stages share the same aligned value.
- Enable tapering when generated context holds identity well but suppresses a new movement at the segment boundary.
- Every segment uses the sampling node's displayed seed.
- `timeline_data` remains compatible; workflows saved before the node namespace rename only need their node types migrated.

See the [node namespace migration guide](docs/NODE_NAMESPACE_MIGRATION.md) for the complete old-to-new mapping.

## Scope and limitations

- The primary target is single-person dance or performance transfer with character and background replacement.
- Motion fidelity is prioritized over maximum segment duration.
- Clean framing, visible limbs, stable frame rate, and consistent source lighting improve results.
- Multi-person occlusion, abrupt cuts, extreme camera motion, and poor source compression remain difficult cases.
- RGB motion transfer is the v1 baseline. Depth and DWPose are intentionally out of scope.
- Generated-tail continuation improves consistency but cannot guarantee perfect identity or a seamless transition in every shot.
- Real model acceptance should be performed in a complete ComfyUI environment before publishing a release tag.

## Technical references and attribution

- Based on the upstream [ComfyUI-MiniMaxH3-TimelineDirector](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector) baseline at `e4d6d5e`.
- Drift-Control AV is adapted from [ComfyUI-MiniMaxH3-Contex-Loop](https://github.com/ethanfel/ComfyUI-MiniMaxH3-Contex-Loop) under GPL-3.0.
- The Omni bridge and prompt workflow reference [MiniMax-H3-Prompt-Rewriter-ComfyUI](https://github.com/pytraveler/MiniMax-H3-Prompt-Rewriter-ComfyUI).
- Official model and prompt guidance: [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3).

## License

[GPL-3.0](LICENSE)
