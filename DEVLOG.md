## Stage #1.0

**Created and tested an initial config-driven pipeline**
 - Created the UV project and folder structure. 
 - Organiced the initial README.md with my project overview.
 - Created a publish_json file and a config.py inside src/houdini_usd_publisher/core/ that properly reads from the .json file.
 - Did some tests inside tests/ for config.py. 

---

## Stage #1.1
**Created and tested a packaging system, exporter wrapper and a Publisher file that glues the system**

 - Created an exporter.py file that exports an USD asset from Houdini using the software LOP nodes. Built tests accordingly. 
 - Created a packager.py that builds the filesystem and copies the main files and subfiles into the apropiate directory. Built tests accordingly. 
 - Created a publisher.py that calls all other methods to perform a full export, validation and package of an USD asset. 
 - Inside publisher.py created a PublishResult to represent the result of the operation. 
 - Built tests accordingly for publisher.py.
 - Tested the operation by creating a new Houdini project and deploying my project inside a Python Shell. Result can be viewed inside houdini_rountrip__test/. 
 - Updated README with installation process inside Houdini. 
 - Added DEVLOG file.

---

## Stage #2.0
**Added basic validation rules and performed tests accordingly. 
Added a CLI entry point - Parse Arguments, load config and Publisher, added dry-run interception**

 - Wrote a base validator to handle all validations. 
 - Added a defaultPrim validation to ensure an USD file is created with a correct defaultPrim setup. Performed tests accordingly.
 - Added a metadata validator to ensure correct metadata for AssetName and Version are generated in the USD file. Tested accordingly.
 - Added a variant set validator to handle variant sets existance and values within those variant sets. Perfomed testing on this as well.
 - Added a CLI entry point. Added parse_args to manage user inputs and compare with my config. Creates and runs a Publisher. Creates a temporary directory to validate and delivers a result. 

---

## Stage #3.0
**Worked on the UI to be used inside Houdini**

 - Made a Houdni panel with Pyside2 and 6 for compatibility. Used a Dummy panel for preview and development.
 - Created an environment variable for root path. Added a browse button to let the user customize the export route. 

### 1. Provisional Deployment instructions: 
-   Launch Houdini
-   Open houdini project: houdini-usd-publisher/houdini/project_test_file/python_tool_test.hipnc
-   Switch to Stage Network

### 2. Add Project to Python Path

-   Open Python Shell and run:

``` python
import sys
import os
sys.path.insert(0, "/path/to/houdini-usd-publisher/src")
os.environ["USD_PUBLISHER_ROOT"] = "/path/to/houdini-usd-publisher"
```

### 3. Add Project to Python Path
-   Add new tab: New Pane tab type > USD Publisher
-   Fill required fields for Asset Name, Version and LOP Node.
-   Browse a root to publish your files.
-   Dry-run the publisher to validate your settings before publishing.
-   Publish your files.


Next Steps:
1. MongoDB registry: class requirement.
2. Scene testing: Pixar Kitchen Set, stress test existing validators, also try Houdini raw file.
3. Additional validators: informed by what the scene exposed
4. Auto-fix: both the fix() method and UI integration
5. Package installer: using installHouPackage as reference
6. README: final deployment
7. Possible additional features like Maya implementation of the tool.
