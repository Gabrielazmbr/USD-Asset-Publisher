# Houdini USD Asset Publisher

For this project I want to explore USD assets, their benefits, their improvement opportunities and their relevance in the industry. In accordance to this I want to achieve a Pipeline TD tool for publishing procedurally generated Houdini assets as correctly structured USD files, following industry-standard conventions for layers, variants, payloads, and metadata.

---

## Project Overview

This tool is meant to live inside Houdini as a Python shelf tool / PyQt panel and allows an artist to publish any Houdini geometry or HDA as a production ready USD asset with a single click. The tool automates the assembly of a USD layer stack that would otherwise require significant manual setup, ensuring consistency across an asset library.

---

## Intended Features

- Export Houdini geometry as a structured USD asset with separate layers:
  - `payload.usda` — geometry, subsetted and ready to be loaded on demand
  - `materials.usda` — material bindings (stubbed for extension)
  - `asset.usda` — top-level assembly file that references payload and materials
- Automatic **variant set** generation (e.g. LOD: `low`, `mid`, `high`)
- Correct **payload arcs** so assets can be referenced into shots without loading geometry immediately
- **Metadata** baked into the root prim: asset name, author, version, publish date
- PyQt UI panel inside Houdini for artist-friendly publishing
- Validation step before export. Checks naming conventions, required prim paths, and material binding presence
- CLI publishing script for headless / farm use

---

## Technology

| Tool | Purpose |
|------|---------|
| Houdini 21.x (LOPs) | Source DCC and USD authoring environment |
| Python 3.10+ | Tool scripting |
| `pxr.Usd` (OpenUSD) | USD layer and stage authoring |
| PyQt | Houdini panel UI |
| pytest | Test-driven development and validation tests |
| Houdini Package | Deployment / installation |

---

## USD Structure Idea

A published asset produces the following file structure:

```
assets/
└── <asset_name>/
    └── v001/
        ├── asset.usda          ← top-level assembly (references payload + materials)
        ├── payload.usda        ← geometry payload
        └── materials.usda      ← material layer (stubbed)
```

Example `asset.usda`:

```usda
#usda 1.0
(
    defaultPrim = "AssetName"
    upAxis = "Y"
    customLayerData = {
        string asset_name = "AssetName"
        string author = "artist"
        string version = "v001"
    }
)

def Xform "AssetName" (
    kind = "component"
    variants = {
        string lod = "mid"
    }
    variantSets = ["lod"]
    payload = @./payload.usda@</AssetName>
)
{
    variantSet "lod" = {
        "low"  { ... }
        "mid"  { ... }
        "high" { ... }
    }
}
```

---

## Testing

Tests are written with `pytest` and cover:

- USD output structure validation (correct prim paths, layer references, payload arcs)
- Variant set presence and switchability
- Metadata correctness
- Naming convention enforcement
- CLI argument handling

---

## Project Initial Structure Development

```
houdini-usd-publisher/
├── package/
│   └── usd_publisher.json      ← Houdini package definition
├── python/
│   ├── publisher/
│   │   ├── __init__.py
│   │   ├── exporter.py         ← USD layer assembly logic
│   │   ├── validator.py        ← pre-publish validation rules
│   │   └── metadata.py         ← metadata schema
│   └── ui/
│       └── panel.py            ← PyQt5 Houdini panel
├── shelf/
│   └── usd_publisher.shelf     ← Houdini shelf tool definition
├── tests/
│   ├── test_exporter.py
│   ├── test_validator.py
│   └── fixtures/
├── publish.py                  ← CLI entry point
├── README.md
└── docs/
    └── design.md               ← pipeline design document
```

---

## Assessment Checklist

| Criteria | Implementation |
|-----------|---------------|
| Test Driven Development | `pytest` suite covering all publish and validation logic |
| Design of solution | USD layer stack design documented in `docs/design.md` |
| Development with suitable tools | Houdini - OpenUSD - PyQt5 |
| Documentation | README - inline docstrings - design doc |
| Deployment | Houdini Package - single file copy, no manual setup |

