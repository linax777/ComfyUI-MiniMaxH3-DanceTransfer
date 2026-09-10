# Dance Node and Repository Namespace Migration

## Objective

Allow the upstream TimelineDirector plugin and this dance-transfer fork to be
installed in the same ComfyUI instance without either plugin overwriting the
other plugin's node registrations, frontend hooks, localization namespaces, or
workflow node types.

The fork repository will be named `ComfyUI-MiniMaxH3-DanceTransfer`. Its owned
ComfyUI node IDs will use the `MiniMaxH3Dance` prefix and its display names will
start with `MiniMax H3 Dance`.

## Public namespace

All 13 plugin-owned node IDs change as one atomic migration:

| Current node ID | New node ID |
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

Python class names will match their new IDs. Plugin-owned categories change to
`MiniMax H3 Dance`, `MiniMax H3 Dance/Long Video`,
`MiniMax H3 Dance/Experimental`, and `MiniMax H3 Dance/Internal` as applicable.
The planner, encoder, and compatibility director will no longer share the
upstream `model/conditioning/minimax` category.

Native ComfyUI nodes such as `MiniMaxH3AddGuide`, `MiniMaxH3ImageToVideo`, and
`MiniMaxH3SigmaShift` are external dependencies and must not be renamed.

## Compatibility policy

No aliases for the 13 former IDs will be registered. An alias would recreate
the collision with the upstream plugin and defeat the migration's purpose.

All workflows and API fixtures tracked in this repository will be migrated to
the new node IDs. Third-party or locally saved workflows created from the
pre-rename `dance-dev` branch must replace plugin-owned node types using the
mapping above. Their timeline JSON, widget values, inputs, and outputs remain
unchanged.

The frontend will recognize only the new planner/director IDs. Localization
roots and node definition keys will also move to the dance namespace so the
upstream and fork translations can coexist.

## Repository identity

After code, workflow, and test migration passes:

1. Push the renamed-node commit to `dance-dev` under the current repository.
2. Rename the GitHub repository from
   `linax777/ComfyUI-MiniMaxH3-TimelineDirector` to
   `linax777/ComfyUI-MiniMaxH3-DanceTransfer`.
3. Update the local `origin` URL and repository-owned links/metadata.
4. Rename the local clone directory to `ComfyUI-MiniMaxH3-DanceTransfer`.
5. Verify the new remote URL resolves and `origin/dance-dev` equals local HEAD.

The upstream remote remains
`https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector.git` because it
continues to identify the source project and immutable baseline.

## Verification

Tests will establish that:

- every registered plugin-owned ID begins with `MiniMaxH3Dance`;
- no registered plugin-owned ID overlaps the 13 upstream IDs;
- expanded graphs use the renamed internal and encoder node types;
- JavaScript hooks and both locale roots use the renamed IDs;
- all tracked workflow/API JSON files use new IDs for plugin-owned nodes;
- native ComfyUI `MiniMaxH3...` dependency IDs remain unchanged;
- existing dance configuration and 24-frame continuation tests still pass;
- Python and JavaScript syntax plus every tracked JSON file remain valid.

The GitHub repository rename is performed only after local verification and
the initial push. No release tag is created by this migration.
