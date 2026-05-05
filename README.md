# Houdini USD Asset Publisher

## Overview

This project explores the practical use of USD (Universal Scene Description) in a production context by developing a pipeline-oriented publishing tool inside Houdini.

The tool focuses on **validating, structuring, and publishing USD assets**. It acts as a pipeline layer on top of Houdini’s native USD workflows, ensuring that assets are consistent, correctly structured, and ready for downstream use.

The system combines Houdini’s LOP-based USD authoring with low-level inspection using OpenUSD (`pxr.Usd`), bridging artist workflows and pipeline validation.

---

## Core Concept


```
[ Artist builds asset in Houdini ]
            ↓
[ Publish Tool Trigger ]
            ↓
[ USD Export via Houdini ]
            ↓
[ Load USD with OpenUSD (pxr.Usd) ]
            ↓
[ Run Validation Rules (config-driven) ]
            ↓
[ If valid → Package and publish asset ]
[ If invalid → Report errors and block publish ]
```

This aims to reflect real-world pipelines, where DCCs generate data and pipeline tools enforce and adequate structure and consistency according to specific needs.

---

## Goals

* Develop a **Pipeline tool** for USD asset publishing
* Enforce **consistent USD structure and conventions**
* Implement a **rules-based validation system** configurable per project
* Bridge **Houdini Solaris workflows** with **OpenUSD inspection**
* Provide both **interactive (UI)** and **automated (CLI)** publishing

---

## Key Features

### 1. Validation-Driven Publishing

Assets are validated before publishing using a configurable rule system:

* Stage integrity (e.g. `defaultPrim`, stage validity)
* Prim hierarchy and structure
* Variant sets (e.g. LOD)
* Metadata presence
* Basic material binding checks

Validation results are categorized as:

* **Error** : blocks publishing
* **Warning** : allows publishing with feedback

---

### 2. Rules-Based Configuration

Publishing behavior is driven by a configuration file:

```
config/publish_config.json
```

This allows:

* different asset structures per project
* customizable validation rules
* flexible variant definitions

Example (simplified):

```json
{
  "variants": {
    "lod": ["low", "mid", "high"]
  },
  "metadata": {
    "required_fields": ["asset_name", "version"]
  }
}
```

Main Reference for my validation rules system: https://github.com/usd-wg/assets/blob/main/docs/asset-structure-guidelines.md 

---

### 3. Structured USD Packaging

Validated assets are published into a consistent structure like this one:

```
assets/
└── <asset_name>/
    └── v001/
        ├── asset.usda
        ├── payload.usda
        └── materials.usda
```

This separation follows USD best practices:

* **asset.usda** : top-level composition
* **payload.usda** : geometry (load-on-demand)
* **materials.usda** : shading data


Main Reference for my USD structure system: https://github.com/usd-wg/assets/blob/main/docs/asset-structure-guidelines.md 

---

### 4. Houdini + OpenUSD Integration

* Houdini (LOPs) is used to **author and export USD**
* OpenUSD (`pxr.Usd`) is used to:

  * inspect stages
  * validate structure
  * enforce pipeline rules


---

### 5. CLI and UI Support

* **CLI (`publish.py`)**
  Enables automated publishing and testing:

  ```bash
  hython publish.py --asset tree --version v001
  ```

* **Houdini UI Panel**
  Provides an artist-friendly interface for publishing and validation feedback

---

## Project Structure

```
houdini-usd-publisher/
├── python/usd_publisher/
│   ├── core/           ← pipeline orchestration (export, package, config)
│   ├── validation/     ← rule-based validation system
│   ├── usd/            ← OpenUSD helpers (stage inspection)
│   ├── ui/             ← Houdini panel
│   └── utils/
│
├── config/
│   └── publish_config.json
│
├── tests/
│   └── fixtures/
│
├── publish.py          ← CLI entry point
└── package/            ← Houdini package definition
```

---

## Testing

Tests are written using `pytest` and executed with Houdini’s Python environment:

```bash
hython -m pytest
```

Testing focuses on:

* validation rules
* USD structure correctness
* pipeline flow

Using `hython` ensures compatibility with Houdini’s USD environment.

---

## Design Principles

* **Validation**
  The tool does not replace Houdini’s USD system, but enforces correctness on top of it.

* **Separation of concerns**
  Export, validation, and packaging are independent modules.

* **Configurable**
  Rules and structure are driven by external configuration.

* **Pipeline-oriented thinking**
  Designed to simulate real workflows.

---

## Requirements
- Houdini (Solaris / LOPs)
- Python (bundled with Houdini)


---
