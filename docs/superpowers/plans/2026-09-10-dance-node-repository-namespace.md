# Dance Node and Repository Namespace Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename every plugin-owned ComfyUI node and the fork repository so the dance fork can run beside the upstream TimelineDirector without registration collisions.

**Architecture:** Put the 13 owned IDs and four category names in one pure Python namespace module, then consume those constants from schemas, graph expansion, and root registration. Mirror the namespace in JavaScript/locales and migrate every tracked workflow fixture atomically; preserve native ComfyUI `MiniMaxH3...` dependency IDs. Rename GitHub and the local clone only after code and workflow verification passes.

**Tech Stack:** Python 3.10+, ComfyUI v3 node schemas, JavaScript ES modules, JSON workflows/locales, pytest, Node test runner, Git, GitHub web UI.

**Spec:** `docs/superpowers/specs/2026-09-10-dance-node-repository-namespace-design.md`

## Global Constraints

- GitHub repository name is exactly `ComfyUI-MiniMaxH3-DanceTransfer`.
- Every plugin-owned node ID starts with exactly `MiniMaxH3Dance`.
- Every plugin-owned display name starts with `MiniMax H3 Dance`.
- Do not register aliases for any of the 13 former IDs.
- Do not rename native ComfyUI dependencies such as `MiniMaxH3AddGuide`, `MiniMaxH3ImageToVideo`, or `MiniMaxH3SigmaShift`.
- Keep upstream remote URL unchanged.
- Keep `dance-baseline` at `e4d6d5e`.
- Do not create a release tag.

---

### Task 1: Establish the owned namespace contract

**Files:**
- Create: `dance_namespace.py`
- Create: `tests/test_dance_namespace.py`

**Interfaces:**
- Produces: `DANCE_NODE_IDS: dict[str, str]`, `DANCE_CATEGORIES: dict[str, str]`, `UPSTREAM_OWNED_NODE_IDS: frozenset[str]`.
- Consumed by: root registration, Python node schemas, and graph expansion in Task 2.

- [ ] **Step 1: Write failing pure tests**

Create tests that load `dance_namespace.py` by file path and assert the exact 13 values:

```python
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

assert namespace.DANCE_NODE_IDS == EXPECTED
assert set(EXPECTED.values()).isdisjoint(namespace.UPSTREAM_OWNED_NODE_IDS)
assert all(value.startswith("MiniMaxH3Dance") for value in EXPECTED.values())
```

Also assert exact categories:

```python
assert namespace.DANCE_CATEGORIES == {
    "root": "MiniMax H3 Dance",
    "long_video": "MiniMax H3 Dance/Long Video",
    "experimental": "MiniMax H3 Dance/Experimental",
    "internal": "MiniMax H3 Dance/Internal",
}
```

- [ ] **Step 2: Run the tests and confirm the missing-module failure**

Run from an isolated temporary directory to avoid pytest importing the hyphenated plugin folder as a package:

```bash
test_dir=$(mktemp -d /tmp/h3-dance-namespace.XXXXXX)
cp tests/test_dance_namespace.py "$test_dir/"
DANCE_PROJECT_ROOT="$PWD" uv run --no-project --with pytest pytest "$test_dir" -q
```

Expected: failure because `dance_namespace.py` does not exist.

- [ ] **Step 3: Add the pure namespace module**

Create immutable mappings with the values above:

```python
from types import MappingProxyType

DANCE_NODE_IDS = MappingProxyType({...})
DANCE_CATEGORIES = MappingProxyType({...})
UPSTREAM_OWNED_NODE_IDS = frozenset({
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
})
```

- [ ] **Step 4: Run the isolated namespace tests**

Expected: all namespace tests pass.

- [ ] **Step 5: Commit**

```bash
git add dance_namespace.py tests/test_dance_namespace.py
git commit -m "test: define collision-free dance node namespace"
```

---

### Task 2: Rename Python registrations, classes, schemas, and expanded graph nodes

**Files:**
- Modify: `__init__.py`
- Modify: `minimax_h3_timeline_director.py`
- Modify: `minimax_h3_finite_segments.py`
- Modify: `experimental_latent_guide.py`
- Modify: `tests/smoke_media_pipeline.py`
- Modify: `tests/smoke_finite_segments.py`
- Modify: `tests/smoke_latent_guide.py`
- Modify: `tests/smoke_i18n.py`
- Modify: `tests/test_dance_namespace.py`

**Interfaces:**
- Consumes: `DANCE_NODE_IDS` and `DANCE_CATEGORIES` from Task 1.
- Produces: the complete collision-free Python runtime namespace and renamed internal graph `class_type` values.

- [ ] **Step 1: Extend the failing namespace test to inspect runtime sources**

Read the four runtime Python files as text and assert every former owned ID is
absent as a quoted registration/schema/graph string. Assert `__init__.py` uses
all 13 new IDs and does not expose old class imports. Separately assert these
native strings remain present:

```python
assert '"MiniMaxH3AddGuide"' in timeline_source
assert '"MiniMaxH3SigmaShift"' not in namespace.UPSTREAM_OWNED_NODE_IDS
```

Run the isolated test and expect failure on the old owned IDs.

- [ ] **Step 2: Rename all 13 Python classes**

Apply the exact ID mapping from the spec to class declarations, imports,
`NODE_CLASS_MAPPINGS`, `NODE_DISPLAY_NAME_MAPPINGS`, tests, and direct class
method calls. Do not change helper function names or timeline JSON fields.

- [ ] **Step 3: Consume namespace constants in schemas and graph expansion**

For each schema, use:

```python
from .dance_namespace import DANCE_CATEGORIES, DANCE_NODE_IDS

node_id=DANCE_NODE_IDS["timeline_planner"]
category=DANCE_CATEGORIES["root"]
```

For expanded nodes, use keys rather than literals:

```python
encoder = graph.node(DANCE_NODE_IDS["timeline_encoder"], ...)
continuation = graph.node(DANCE_NODE_IDS["finite_latent_continuation"], ...)
finalized = graph.node(DANCE_NODE_IDS["finite_segment_finalize"], ...)
```

Leave `SamplerCustomAdvanced`, `BasicGuider`, `RandomNoise`, `VAEDecode`,
`AudioConcat`, `ImageBatch`, and all native MiniMax node IDs unchanged.

- [ ] **Step 4: Update root mappings and display names**

Every key must come from `DANCE_NODE_IDS`; every display name must start with
`MiniMax H3 Dance`. Change the module docstring and Python logger prefix to the
dance name.

- [ ] **Step 5: Update Python smoke expectations**

Rename class references and expected expanded `class_type` values. Add explicit
assertions that `NODE_CLASS_MAPPINGS` is disjoint from
`UPSTREAM_OWNED_NODE_IDS` when loaded under a real ComfyUI runtime.

- [ ] **Step 6: Run pure tests and compile all changed Python modules**

```bash
DANCE_PROJECT_ROOT="$PWD" uv run --no-project --with pytest --with torch --with numpy pytest "$test_dir" -q
uv run --no-project --with torch python -m py_compile \
  dance_namespace.py minimax_h3_timeline_director.py \
  minimax_h3_finite_segments.py experimental_latent_guide.py
```

Expected: tests and compilation pass. Record that runtime smoke scripts still
require the external ComfyUI `server` and `comfy_api` packages.

- [ ] **Step 7: Commit**

```bash
git add __init__.py dance_namespace.py minimax_h3_timeline_director.py \
  minimax_h3_finite_segments.py experimental_latent_guide.py tests
git commit -m "refactor: isolate dance node registrations"
```

---

### Task 3: Rename frontend hooks, localization namespaces, and workflows

**Files:**
- Modify: `js/minimax_h3_timeline_director.js`
- Modify: `locales/en/main.json`
- Modify: `locales/en/nodeDefs.json`
- Modify: `locales/zh/main.json`
- Modify: `locales/zh/nodeDefs.json`
- Modify: `example_workflows/*.json`
- Modify: `tests/experiments/minimax_h3_latent_guide_ab_api.json`
- Modify: `tests/experiments/run_minimax_h3_finite_segments.py`
- Modify: `tests/test_dance_workflow.py`
- Modify: `tests/smoke_i18n.py`
- Modify: `tests/test_dance_namespace.py`

**Interfaces:**
- Consumes: exact new IDs from Task 1.
- Produces: frontend and serialized artifacts that resolve only to dance-owned node IDs.

- [ ] **Step 1: Add failing artifact assertions**

Extend `tests/test_dance_namespace.py` to load JavaScript, locale JSON, every
tracked workflow JSON, and the experiment API JSON. Assert:

```python
assert "MiniMaxH3DanceTimelinePlanner" in javascript
assert "MiniMaxH3TimelinePlanner" not in javascript
assert set(en_node_defs) == set(zh_node_defs) == set(DANCE_NODE_IDS.values())
assert "MiniMaxH3DanceTimelineDirector" in en_main
```

Walk every workflow/API JSON recursively, collect values under `type` and
`class_type`, and reject only values in `UPSTREAM_OWNED_NODE_IDS`. Confirm native
`MiniMaxH3AddGuide` occurrences remain unchanged in the experiment fixture.
Run and expect failure before migration.

- [ ] **Step 2: Migrate JavaScript identity**

Change `TIMELINE_NODE_NAMES` to the dance planner/director IDs. Change the
localization lookup root and console/logger prefixes to
`MiniMaxH3DanceTimelineDirector`. Keep the source filename and timeline data
format unchanged.

- [ ] **Step 3: Migrate both locale trees**

Rename all 13 `nodeDefs.json` top-level keys. Change `main.json` root from
`MiniMaxH3TimelineDirector` to `MiniMaxH3DanceTimelineDirector`. Prefix every
localized display name with `MiniMax H3 Dance` while preserving translated
input/output descriptions.

- [ ] **Step 4: Migrate serialized node types**

Apply exact-string substitutions for the 13 owned IDs across `example_workflows`,
`tests/experiments`, and workflow tests. Do not perform a broad
`MiniMaxH3` replacement because native nodes must remain unchanged. Update
`aux_id` values to `linax777/ComfyUI-MiniMaxH3-DanceTransfer`.

- [ ] **Step 5: Run frontend and artifact verification**

```bash
node --test tests/dance_continuation_state.test.mjs
node --check js/dance_continuation_state.mjs
node --check js/minimax_h3_timeline_director.js
for file in locales/en/*.json locales/zh/*.json example_workflows/*.json tests/experiments/*.json; do
  python3 -m json.tool "$file" >/dev/null || exit 1
done
```

Run the isolated Python tests and expect the namespace/workflow assertions to pass.

- [ ] **Step 6: Commit**

```bash
git add js locales example_workflows tests
git commit -m "refactor: migrate dance frontend and workflows"
```

---

### Task 4: Update fork package identity and migration documentation

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `README_CN.md`
- Modify: `docs/dance-conditioning-architecture.md`
- Create: `docs/NODE_NAMESPACE_MIGRATION.md`
- Modify: other tracked Markdown files only where they identify this fork rather than upstream history.

**Interfaces:**
- Consumes: final public namespace from Tasks 1–3.
- Produces: install instructions and migration reference for the renamed fork.

- [ ] **Step 1: Add metadata assertions**

Extend the pure namespace test to assert:

```python
assert 'name = "comfyui-minimax-h3-dance-transfer"' in pyproject
assert 'DisplayName = "MiniMax H3 Dance Transfer"' in pyproject
assert "github.com/linax777/ComfyUI-MiniMaxH3-DanceTransfer.git" in readme
```

Run and expect failure on current package metadata.

- [ ] **Step 2: Update package and README identity**

Set the package name and display name above. Change the English heading to
`ComfyUI MiniMax H3 Dance Transfer` and the Chinese heading to
`ComfyUI MiniMax H3 舞蹈遷移`. Point clone instructions to the new fork URL and
search instructions to `MiniMax H3 Dance`.

Keep upstream release-asset URLs and attribution pointing at Songssx because
those assets and historical authorship still belong to upstream.

- [ ] **Step 3: Write the migration guide**

Document the 13-entry old/new table, explain that no old aliases exist, and
tell users of pre-rename dance workflows to replace the node type according to
the table. State that ordinary widget values and `timeline_data` require no
conversion.

- [ ] **Step 4: Run metadata and documentation checks**

Run the isolated tests, `git diff --check`, and search for old fork installation
URLs. Confirm any remaining Songssx URL is explicitly upstream attribution,
release media, baseline history, or the unchanged `upstream` remote.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md README_CN.md docs tests/test_dance_namespace.py
git commit -m "docs: rename fork as MiniMax H3 Dance Transfer"
```

---

### Task 5: Verify, push, and rename the repository

**Files:**
- No source changes expected.
- Rename local directory after remote verification.

**Interfaces:**
- Consumes: verified commits from Tasks 1–4.
- Produces: GitHub repository and local clone named `ComfyUI-MiniMaxH3-DanceTransfer`.

- [ ] **Step 1: Run the final local verification suite**

Copy `test_dance_segments.py`, `test_dance_workflow.py`,
`test_evaluate_motion.py`, and `test_dance_namespace.py` into one fresh
temporary directory and run them with pytest, torch, and numpy. Run all Node
tests, Python compilation, JSON validation, `git diff --check`, and confirm
`git status --short` is empty.

- [ ] **Step 2: Verify immutable baseline and namespace diff**

```bash
git rev-parse dance-baseline
git show -s --format=%s dance-baseline
git log --oneline dance-baseline..HEAD
```

Expected SHA: `e4d6d5ea44eb00e2414d16dd94883be8e2661213`.

- [ ] **Step 3: Push code under the current remote identity**

```bash
git push origin dance-dev
```

Verify local HEAD equals `origin/dance-dev`.

- [ ] **Step 4: Rename the GitHub repository**

Using the authenticated GitHub browser session, open repository settings and
rename exactly:

```text
linax777/ComfyUI-MiniMaxH3-TimelineDirector
→ linax777/ComfyUI-MiniMaxH3-DanceTransfer
```

Do not change visibility, default branch, topics, issues, or permissions.

- [ ] **Step 5: Update and verify the local origin**

```bash
git remote set-url origin https://github.com/linax777/ComfyUI-MiniMaxH3-DanceTransfer.git
git fetch origin dance-dev
git rev-parse HEAD
git rev-parse origin/dance-dev
git remote -v
```

Expected: both revisions match and upstream still targets Songssx.

- [ ] **Step 6: Rename the local clone directory**

From the parent directory, rename only the explicit clone path:

```bash
mv ComfyUI-MiniMaxH3-TimelineDirector ComfyUI-MiniMaxH3-DanceTransfer
```

Verify the new directory contains `.git`, is on `dance-dev`, and has a clean
status. Do not rename the outer workspace directory.

- [ ] **Step 7: Report release boundary**

Report the new GitHub URL, local path, HEAD, passed test counts, and the ComfyUI
runtime smoke-test limitation. Do not create `v0.1-dance`; real ComfyUI/model
acceptance remains a separate gate.
