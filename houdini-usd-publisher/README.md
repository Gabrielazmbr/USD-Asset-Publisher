# Houdini USD Asset Publisher

This project explores the practical use of USD (Universal Scene Description) in a production context by developing a pipeline-oriented publishing tool inside Houdini.

The tool focuses on **validating, structuring, and publishing USD assets**. It acts as a pipeline layer on top of Houdini’s native USD workflows, ensuring that assets are consistent, correctly structured, and ready for downstream use.

The system combines Houdini’s LOP-based USD authoring with low-level inspection using OpenUSD (`pxr.Usd`), bridging artist workflows and pipeline validation with a button. 

---

## Table of Contents

- [Overview](#overview)
- [Design Philosophy](#design-philosophy)
- [Architecture](#architecture)
- [Validation System](#validation-system)
- [Auto-Fix System](#auto-fix-system)
- [Configuration](#configuration)
- [Houdini UI Panel](#houdini-ui-panel)
- [MongoDB Registry](#mongodb-registry)
- [Published Asset Structure](#published-asset-structure)
- [CLI Usage](#cli-usage)
- [Installation](#installation)
- [Test Suite](#test-suite)
- [Real Scene Testing](#real-scene-testing)
- [Development Decisions](#development-decisions)
- [Known Limitations](#known-limitations)

---

## Overview

While Houdini’s export tools generate USD reliably, they don’t automatically enforce custom pipeline conventions. Small omissions such as missing metadata or variant sets, may only become noticeable later in production when the asset fails to load downstream.

This tool solves that by adding a validation and packaging layer on top of Houdini's export. The artist builds their asset normally in Solaris, then clicks **Publish** in this panel. Then the tool:

1. Exports the current LOP network to USD via Houdini's ROP node
2. Runs a configurable set of validators against the exported file
3. Optionally applies auto-fixes to correctable errors
4. Packages the validated asset into a versioned folder structure
5. Records the publish to MongoDB Atlas
6. Writes a JSON report alongside the asset

Errors block the publish with specific feedback. Warnings allow the publish with annotation. The artist does not overload thinking about folder structure, naming conventions, or metadata. With just a button they either get a green light or a specific list of things to fix.

---

## Design Philosophy

**Validate the exported file, not the live stage.** The validators run against the on-disk USD file, not the Houdini stage in memory. This means validators have no dependency on `hou`, making them portable and independently testable with `pytest`. It also means validation tests the exact artifact that downstream tools will consume, catching any export inconsistencies in how Houdini serialises to disk.

**Config over hardcoding.** Every pipeline rule — required metadata fields, expected variant sets, up-axis convention, naming style — lives in `publish_config.json`. In this way, the user changes the config, not the code.

**Separation of concerns.** The system is divided into separate modules with distinct responsibilities. For example, exporting, validation, packaging, and database integration are handled independently and tested in isolation.

**Errors block, warnings annotate.** Validators distinguish between pipeline violations (errors, which prevent publish) and best-practice suggestions (warnings, which are recorded but don't block). The split is explicit in every validator.

---

## Architecture

```
houdini-usd-publisher/
├── src/houdini_usd_publisher/
│   ├── core/
│   │   ├── config.py        ← loads publish_config.json
│   │   ├── exporter.py      ← drives Houdini ROP USD export
│   │   ├── packager.py      ← creates versioned folder structure
│   │   ├── publisher.py     ← orchestrates the full pipeline
│   │   ├── registry.py      ← MongoDB publish record
│   │   └── report.py        ← writes publish_report.json
│   ├── validation/
│   │   ├── base.py          ← BaseValidator abstract class
│   │   ├── default_prim.py
│   │   ├── metadata.py
│   │   ├── variant_set.py
│   │   ├── kind.py
│   │   ├── material.py
│   │   ├── up_axis.py
│   │   ├── file_reference.py
│   │   └── naming.py
│   └── ui/
│   │   ├── panel.py         ← Houdini Python Panel (3 tabs)
│   │   └── standalone.py    ← standalone runner for development
│   └── cli.py
├── config/
│   └── publish_config.json
├── tests/
│   ├── conftest.py
│   └── validators/
│       └── (one test file per validator)
├── houdini/ 
│   ├── HoudiniTestProjects  ← Houdini Scene Testing ExampleProject File
│   ├── PublishTesting       ← Houdini Scene Testing .usda files
│   └── ValidateFileTesting  ← Houdini Import Testing .usda file
├── media/                   ← Video Demonstration of the Tool & Testing
├── install.py
├── pyproject.toml
└── README.md
```

### Pipeline Flow

```
Artist finishes asset in Houdini LOPs
              ↓
Publisher.publish() (UI or CLI)
              ↓
USDExporter.export() → tmp .usda via Houdini ROP
              ↓
Auto-fix pass (per-validator policy from config)
              ↓
Validators run against exported file
              ↓
Errors → block publish, return result with errors
              ↓
USDPackager.package() → assets/<name>/<version>/
              ↓
PublishRegistry.record() → MongoDB Atlas
              ↓
PublishReport.write() → publish_report.json
              ↓
PublishResult → UI display or CLI output
```

---

## Validation System

Eight validators, each independently configurable:

| Validator | Errors (blocks) | Warnings | Auto-fix | Config fields |
|---|---|---|---|---|
| `DefaultPrimValidator` | No `defaultPrim` set | — | Sets to first root prim | — |
| `MetadataValidator` | Missing required fields | — | Writes fields from UI | `required_fields` |
| `VariantSetValidator` | Missing required sets | — | No | `required_sets` |
| `KindValidator` | Missing kind on root prim | — | Sets to `component` if missing | — |
| `MaterialValidator` | — | Meshes with no material binding | No | — |
| `UpAxisValidator` | Wrong up-axis | No up-axis set | Changes Axis | `expected_axis` |
| `FileReferenceValidator` | Unresolved file references | — | No | — |
| `NamingConventionValidator` | Reserved name used | Leading/trailing/double underscores, style violations | No | `naming_style`, `allow_*`, `reserved_names` |

### BaseValidator

Every validator inherits from `BaseValidator` and implements `validate(usd_file: Path) -> tuple[list[str], list[str]]` returning errors and warnings respectively. Validators that support auto-fix also implement `fix(usd_file: Path, **kwargs) -> list[str]`, returning readable descriptions of changes made.

### DefaultPrimValidator

Checks that `stage.GetDefaultPrim().IsValid()` returns true. Without a `defaultPrim`, any reference to this asset is ambiguous — USD doesn't know which prim to use as the entry point. Auto-fix sets it to the first root-level prim.

### MetadataValidator

Checks that each field in `required_fields` (from config) exists in the `defaultPrim`'s customData dictionary. Auto-fix writes the values using the asset name and version passed from the UI. This means metadata is always consistent with the publish record.

### VariantSetValidator

Checks that each variant set named in `required_sets` exists on the `defaultPrim`, and that all required variants within it are present. No auto-fix because adding variant sets requires artist decisions about geometry and look content.

### KindValidator

Uses `Usd.ModelAPI` to check that the root prim has a kind assigned. Kind hierarchy (`assembly`, `group`, `component`, `subcomponent`) is how USD identifies what kind of asset a prim represents and enables LOD switching in rendering. Auto-fix sets the root prim to `component` if no kind is present.

### MaterialValidator

Traverses all `UsdGeom.Mesh` prims and checks for a valid `UsdShade.MaterialBindingAPI` binding. Returns a warning (not an error) because in production pipelines materials are commonly separated into referenced layers, which means the binding may not be visible in the root layer alone.

### UpAxisValidator

Reads `UsdGeom.GetStageUpAxis()` and compares against `expected_axis` from config. In a Y-up pipeline, a Z-up asset will render incorrectly. Auto-fix uses `UsdGeom.SetStageUpAxis()` directly.

### FileReferenceValidator

Uses `UsdUtils.ComputeAllDependencies()` to compute all layers, assets, and unresolved paths. Resolves each path and checks it exists on disk. Two production-specific fixes are in place:

- Houdini appends `:SDF_FORMAT_ARGS:format=usda` to sublayer paths. The validator strips this suffix before checking existence so valid files aren't reported as missing.
- `ComputeAllDependencies` includes the root file itself in the layers list. The validator skips it to avoid a false self-reference error.

### NamingConventionValidator

Checks prim names defined in the root layer (skipping referenced and instanced prims, which are the original author's responsibility). Enforces:

- `reserved_names` — names like `default` and `root` that have special meaning in USD (error)
- `allow_leading_underscore` — convention violation (warning)
- `allow_trailing_underscore` — convention violation (warning)
- `allow_double_underscore` — often indicates auto-generated names (warning)
- `naming_style` — `CamelCase`, `snake_case`, or `any` (warning)

No auto-fix: renaming prims changes their paths, which silently breaks any existing references into the asset.

Note: USD rejects names starting with digits and names containing spaces at the parser level, so the validator doesn't check for these as the stage would never open.

---

## Auto-Fix System

Auto-fix is controlled at two levels:

1. **Per-publish call** — the UI and CLI both have an auto-fix toggle
2. **Per-validator policy** — each validator has an `auto_fix` flag in `publish_config.json`

Automatic fixes are controlled per validator through the configuration. This allows some issues, such as missing metadata, to be corrected automatically while others, such as variant set modifications, still require manual intervention. Before applying a fix, the publisher checks config.is_auto_fix_enabled(validator_name).

```json
"MetadataValidator": {
  "enabled": true,
  "auto_fix": true,
  "required_fields": ["asset_name", "version"]
},
"VariantSetValidator": {
  "enabled": true,
  "auto_fix": false,
  "required_sets": { "lod": ["low", "mid", "high"] }
}
```

Applied fixes appear as `FIXED` lines in the UI (cyan) and are recorded in both the `PublishResult` and the `publish_report.json`.

---

## Configuration

All pipeline rules live in `config/publish_config.json`:

```json
{
  "studio": "YourStudio",
  "pipeline_version": "1.0",
  "export_format": "usda",
  "assets_root": "assets",
  "validators": {
    "DefaultPrimValidator": {
      "enabled": true,
      "auto_fix": true
    },
    "MetadataValidator": {
      "enabled": true,
      "auto_fix": true,
      "required_fields": ["asset_name", "version"]
    },
    "VariantSetValidator": {
      "enabled": true,
      "auto_fix": false,
      "required_sets": {
        "lod": ["low", "mid", "high"]
      }
    },
    "KindValidator": {
      "enabled": true,
      "auto_fix": true
    },
    "MaterialValidator": {
      "enabled": true
    },
    "UpAxisValidator": {
      "enabled": true,
      "auto_fix": true,
      "expected_axis": "Y"
    },
    "FileReferenceValidator": {
      "enabled": true
    },
    "NamingConventionValidator": {
      "enabled": true,
      "naming_style": "any",
      "allow_leading_underscore": false,
      "allow_trailing_underscore": false,
      "allow_double_underscore": false,
      "reserved_names": ["default", "root"]
    }
  }
}
```

### PublishConfig API

```python
config = PublishConfig(config_path)

config.export_format                                   # "usda"
config.assets_root                                     # "assets"
config.enabled_validators                              # list of enabled class names
config.is_validator_enabled("DefaultPrimValidator")    # True
config.get_validator_config("MetadataValidator")       # {"enabled": True, "required_fields": [...]}
config.is_auto_fix_enabled("MetadataValidator")        # True
```

### Config Editor Tab

The UI exposes a Config Editor tab where all validator settings can be changed without touching the JSON file directly. The editor exposes:

- Enable/disable toggles per validator
- Auto-fix checkboxes for validators that support it
- Required metadata fields (editable list)
- Required variant sets with variant name lists (add/remove rows)
- Naming style dropdown and allow/deny checkboxes
- Reserved names field
- Expected up-axis setting

Save writes back to `publish_config.json`. Reset reloads from the file.

---

## Houdini UI Panel

The panel has three tabs registered in Houdini's Python Panel system.

### Config Tab

Exposes all validator settings. This is the primary way a pipeline TD configures the tool for a studio — no JSON editing required.

### Publish Tab

The artist workflow:

- Asset name and version fields
- LOP node path (the node whose stage will be exported)
- Publish root with folder browser
- Auto-fix checkbox
- **Dry Run** button — validates and packages to a temp location, shows full results, writes nothing to the publish root or registry
- **Publish** button — full publish to the configured root
- Colour-coded results: `FIXED` (cyan), `ERROR` (red), `WARNING` (yellow), `OK` (green)
- Recent publish history table pulled from MongoDB, auto-refreshed after a successful publish

### Validate File Tab

Validates any USD file without going through the publish workflow. Useful for validating assets received from external sources or checking a file before deciding whether to reference it.

Features:

- File browser for any `.usd`/`.usda`/`.usdc` file
- Asset name and version fields (used by auto-fix to populate metadata)
- Auto-fix checkbox (respects per-validator config policy)
- **Validate** button with colour-coded results
- **Open as Sublayer** — imports the file as a sublayer LOP node (enabled only after successful validation, only active inside Houdini)
- **Open as Reference** — imports the file as a reference LOP node

The two open buttons present artists the possibility of sublayer and reference composition arcs: sublayer merges the file's entire opinion into the current stage; reference brings in a specific prim and allows overrides above it.

---

## MongoDB Registry

Every successful publish writes a document to MongoDB Atlas:

```json
{
  "asset_name": "tree",
  "version": "v001",
  "published_at": "2026-05-18T12:00:00",
  "published_by": "gabrielazambrano",
  "published_path": "/path/to/assets/tree/v001/asset.usda",
  "validators_run": ["DefaultPrimValidator", "MetadataValidator", "..."],
  "warnings": [],
  "fixes": ["defaultPrim set to 'World'"],
  "dry_run": false,
  "success": true
}
```

Registry failures never block a publish — the tool prints a warning and continues. The connection uses `certifi` for SSL certificate verification, which works from both the `uv` virtual environment and Houdini's bundled Python.

Setup requires a `.env` file in the project root:

```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=usd_publisher
```

The `.env` is gitignored. The `USD_PUBLISHER_ROOT` environment variable anchors path resolution so the `.env` is found correctly inside Houdini's environment.

---

## Published Asset Structure

```
assets/
└── tree/
    └── v001/
        ├── asset.usda          ← main file, referenced by shots
        ├── payload.usda        ← heavy geometry (loaded on demand)
        ├── materials.usda      ← shading data
        └── publish_report.json
```

`payload.usda` and `materials.usda` are stubs that keep the composition arcs valid. Houdini's exported `asset.usda` references `./payload.usda` as a payload arc, so without the stub the reference would break on load. Fully populating these stubs would require separate ROP exports for geometry and materials — a pipeline extension noted for future development.

### publish_report.json

```json
{
  "asset_name": "tree",
  "version": "v001",
  "published_at": "2026-05-18T12:00:00",
  "published_by": "gabrielazambrano",
  "published_path": "/path/to/assets/tree/v001/asset.usda",
  "validators_run": [
    "DefaultPrimValidator", "MetadataValidator", "VariantSetValidator",
    "KindValidator", "MaterialValidator", "UpAxisValidator",
    "FileReferenceValidator", "NamingConventionValidator"
  ],
  "warnings": [],
  "fixes": [],
  "registry_recorded": true,
  "success": true
}
```

---

## CLI Usage

The CLI runs via `hython` (Houdini's Python runtime) for full `hou` module access:

```bash
# Full publish
hython -m houdini_usd_publisher.cli \
  --asset tree \
  --version v001 \
  --lop-node /stage/finalize \
  --publish-root /path/to/assets

# Dry run
hython -m houdini_usd_publisher.cli \
  --asset tree \
  --version v001 \
  --dry-run

# With auto-fix
hython -m houdini_usd_publisher.cli \
  --asset tree \
  --version v001 \
  --auto-fix
```

The CLI and the UI panel call the same `Publisher` orchestrator — the UI is a wrapper, not a separate implementation.

---

## Installation

### Prerequisites

- Houdini 20+ (Houdini 21 tested)
- Python 3.11+ (managed via `uv`)
- MongoDB Atlas account (optional — tool works without it)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/houdini-usd-publisher.git
cd houdini-usd-publisher

# 2. Install Python dependencies
pip install uv
uv pip install -e .

# 3. Run the Houdini package installer
uv run python install.py
# or from inside Houdini:
# hython install.py

# 4. Restart Houdini

# 5. Open the panel: Panes (+) → New Pane Tab Type → USD Asset Publisher

# 6. (Optional) Set up MongoDB
cp .env.example .env
# Edit .env with your MongoDB Atlas URI
```

The installer detects your Houdini version and preferences folder automatically. It writes:

- A package JSON to `~/houdini21.x/packages/` — adds `src/` to `PYTHONPATH`
- A `.pypanel` file to `~/houdini21.x/python_panels/` — registers the panel

### Environment Variable

Set `USD_PUBLISHER_ROOT` to the repository root:

```bash
export USD_PUBLISHER_ROOT=/path/to/houdini-usd-publisher
```

This anchors all path resolution (config file, `.env` loading) so the tool works correctly inside Houdini's environment, where the working directory may not be the project root.

---

## Test Suite

Tests are run without Houdini using `uv run pytest`. All validators use `pxr.Usd` directly — no `hou` dependency.

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific validator's tests
uv run pytest tests/validators/test_default_prim.py -v
```

**104 tests, all passing.**

### Test Architecture

Each validator has its own test file under `tests/validators/`. Tests write inline USDA content to `tmp_path` fixtures rather than relying on checked-in test assets, making them self-contained and fast.

The critical fixture is `fresh_config` in `tests/conftest.py`. The Config Editor UI can write changes back to `publish_config.json` at runtime — if tests used the real config file, a UI session where the artist changed settings would break the test suite. `fresh_config` creates an isolated config from a known-good JSON string for each test that needs it:

```python
@pytest.fixture
def fresh_config(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(KNOWN_GOOD_CONFIG)
    return PublishConfig(config_path)
```

### Test Coverage by Module

| Module | Tests | Notes |
|---|---|---|
| `config.py` | 12 | Includes disabled validator, malformed JSON |
| `exporter.py` | 8 | Mocked — no Houdini required |
| `packager.py` | 10 | Filesystem checks |
| `publisher.py` | 14 | Patches exporter with valid fake USD |
| `registry.py` | 8 | Mocked MongoDB connection |
| `report.py` | 6 | JSON output validation |
| `test_autofix.py` | 8 | Cross-validator auto-fix sequence |
| Validators | 38 | Inline USDA fixtures per test |

---

## Real Scene Testing

A complete real-scene validation workflow was recorded in Houdini and submitted as part of this project. The test session demonstrates each validator catching the error it was designed to catch, then auto-fixing where applicable.

### Validators Tested in Houdini

Each validator was tested by deliberately creating a scene that would fail, running a dry run to confirm the error is caught, then either fixing the scene or enabling auto-fix.

### Validate File Tab — Pixar Kitchen Set

The Pixar USD Kitchen Set (`Kitchen_set.usd`) was validated against the studio config to demonstrate validation of externally received assets:

```
✗ INVALID
ERROR   Missing required metadata field: 'asset_name'
ERROR   Missing required metadata field: 'version'
ERROR   Missing required variant set: 'lod'
ERROR   Stage upAxis is 'Z' — expected 'Y'
WARNING Found 1788 Mesh prim(s) but no Material prims
```

This is correct — the Kitchen Set was authored by Pixar for different pipeline conventions. The validation output tells the user exactly what needs to change before the asset enters their pipeline. With auto-fix enabled, metadata is written automatically; the remaining issues (variant sets, up-axis) are flagged for artist attention.

> A video walkthrough of the full real-scene testing session is included in the project submission.

---

## Development Decisions

**Why validate the exported file rather than the live Houdini stage?** Validators use only `pxr.Usd` — no `hou` dependency. This makes them testable with `pytest` without Houdini, portable to non-Houdini contexts, and ensures the exact artifact that downstream tools consume is what gets validated.

**Why is `VariantSetValidator` not auto-fixable?** Variant sets contain geometry, look assignments, and overrides that are the artist's work. Silently creating empty variant sets to pass validation would produce a technically-valid but artistically-empty asset. The artist must fix this.

**Why does `MaterialValidator` warn rather than error?** Production pipelines separate materials into referenced layers. The root layer may genuinely have no material prims — they're in `materials.usda`, which is referenced in. An error would produce false positives on valid production assets.

**Why does `NamingConventionValidator` not check for spaces or leading digits?** USD rejects these at the parser level — a stage with such a prim name will fail to open at all. The validator would never run.

**Why does `NamingConventionValidator` only check root layer prims?** Referenced and instanced content was authored by someone else. Flagging their naming conventions creates noise without any actionable path for the current artist to fix it.

**Why does `FileReferenceValidator` strip `:SDF_FORMAT_ARGS:`?** Houdini appends format hints to sublayer paths. `ComputeAllDependencies` returns these raw paths in the unresolved list, but the file exists if you strip the suffix. Without this fix, every Houdini-exported file with sublayers produces false errors.

---

## Future Improvements

The stub files (payload.usda, materials.usda) are empty placeholders. Fully populating them would require multiple ROP exports separating geometry and materials into distinct files. The stubs prevent the composition arcs from breaking on load.

The CLI produces ModuleNotFoundError: No module named 'hou' if run outside a Houdini session. A graceful error message for this case is noted for future improvement.

**Validation Depth** All validators currently inspect the root layer only. A meaningful extension would be layer-aware validation. Checking opinions across sublayers, identifying conflicts between layers, and validating that stronger layers don't silently override required values set in weaker ones. This would require traversing the full layer stack rather than just the composed result.

**Composition arc validation** The tool currently validates the result of composition (does the stage have a defaultPrim, are the variant sets present) but not the composition arcs themselves. Future validators could check that payload arcs are correctly structured for load-on-demand workflows, that references point to assets with valid defaultPrim settings, and that instanced prims share prototype structure consistently.

**Cross-DCC use** The validation system is entirely independent of Houdini. The validators use only pxr.Usd and operate on USD files on disk so they have no knowledge of how the file was produced. This means the same validation layer could be placed after export from Maya, Blender, or any other DCC that can write USD. The exporter module is the only Houdini-specific component; replacing it with a thin wrapper around another DCC's export would bring the full validation and packaging pipeline to that application without changing any validator code.

---

## Dependencies

```
usd-core
pymongo
certifi
python-dotenv
PySide6
pytest
```

All managed via `uv`. The `certifi` package handles SSL for MongoDB Atlas from both the `uv` environment and Houdini's bundled Python, which doesn't include up-to-date CA certificates.
