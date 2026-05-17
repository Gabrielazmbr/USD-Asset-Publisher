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
 - Created Provisional Deployment instructions:

### 1. Launch: 
-   Launch Houdini
-   Open houdini project: houdini-usd-publisher/houdini/project_test_file/python_tool_test.hipnc
-   Switch to Stage Network

### 2. Add a Python Panel
-   In Houdini: Windows > Python Panel Editor
-   Click 'New Interface', and name it 'usd_publisher', label it 'USD Publisher'
-   Paste the contents of panel.py into the Script tab
-   Click 'Apply'
-   Go to Pane Tab Menu, add 'USD Publisher' to Pane Tab Menu Entries.

### 3. Point Project Path

-   Open Python Shell and run:

``` python
import sys
import os
sys.path.insert(0, "/path/to/houdini-usd-publisher/src")
os.environ["USD_PUBLISHER_ROOT"] = "/path/to/houdini-usd-publisher"
```

### 4. Test Tool
-   Add new tab: New Pane tab type > USD Publisher
-   Fill required fields for Asset Name, Version and LOP Node.
-   Browse a root to publish your files.
-   Dry-run the publisher to validate your settings before publishing.
-   Publish your files.

---

## Stage #4.0
**Worked on integration and Registry**
**Tested my tool against Pixar Kitchen Set and a simple LOP Houdini Scene, added more validators and auto-fix functionality**

1. MongoDB: I created a REGISTRY class to manage and send events to a MongoDB Atlas cluster.This lets me track and log events on publish that then can be accessed in a version History. I added panel support to display this in the Houdini UI. In this window, the user can see Asset, version, publish path and other event details, as well as warnings and validation. This data can also be seen online in the web interface. 
2. Scene testing: I did a stress test on the tool against the Pixar Kitchen Set and a simple LOP Houdini Scene. This revealed more development I had to do on existing validators and marked the route for new validators. 
3. Additional validators: I added a kind validator , that evaluates hierarchy in the USD stage. Rules are explained inside KindValidator Class. Added testing as well. Created a Material validator that checks for meshes and materials inside the stage. It is based on warnings rather than errors. Created an Up_axis validator that checks for the correct up axis. Added testing for these new validators. 
4. Auto-fix: I added an autofix feature to some of the validators that could beneficiate from automatically fixing issues. In this case, defaultPrim, metadata , kind and UpAxis validaors. 

---

## Stage #5.0
**Configurable User Validation Panel**
**Import Validation Panel**
**JSON Validation Report**
**New Validators**

1. I added support for a user configurable validation. The user can choose which rules to apply based on their pipeline and also if wants auto-fix or just validation. I added a new panel that directly modifies houdini-usd-publisher.json. 
2. As my validation is based on already generated USD files, I added an import validator mode in the UI. This lets the user validate an incoming USD file and also auto-fix it if desired, before entering a pipeline. 
3. I added a json validation report that is saved alongside the published asset. This to provide a record of the validation results even if the MondoDB database is not available. 
4. New validators: FileReferenceValidator, NamingConventionValidator. Created to control and fix naming conventions and to validate file references and hierarchy in the USD stage. 


---

## Stage #6.0

- I created an install.py file to ship my tool into a proper package. It finds the Houdini preferences folder, creates a packages/ subfolder if needed and writes the JSON package file there. 

---

- Package Deployment instructions and Tool Testing:

### Installation Requirements:

- Houdini 21.0 (or compatible version)
- Python 3.13
- uv package manager

### 1. Run the Houdini package installer

- Inside Repo and after installing dependencies: In terminal run:
```
uv run python install.py
```
- When prompted, enter your Houdini version (e.g. 21.0):
  - The installer will find your Houdini preferences folder automatically. 
  - Write the package JSON to ~/houdini21.0/packages/ (Mac/Linux) or ~/Documents/houdini/21.0/packages/ (Windows). 
  - Register the USD Publisher panel in ~/houdini21.0/python_panels/.

### 2. Restart/Open Houdini:
- After restarting, open the panel:
  - Windows → Python Panel Editor → Pane Tab Menu.
  - Add "USD Asset Publisher" to Pane Tab Menu Entries.
  - Apply/Acept. 
  - Add new tab: New Pane tab type > USD Publisher

### 3. Restart/Open Houdini:
- Set up MongoDB: 
  - Create a .env file in the project root:
  ```
  MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?appName=<app>
  MONGODB_DATABASE=usd_publisher
  ```
  - Without this, publishing still works but the registry won't record history.

### 4.Verifying the install:
- Run the test suite to confirm everything is working:
  ```
  uv run pytest -v
  ```
- All 99 tests should pass.

### 5. Test Tool:
- Config:
  - Choose the validators you want to use. Enable/disable auto-fixes when applies. 
  - Save Config when you are done. 
- Publish: 
  - Fill required fields for Asset Name, Version and LOP final Node (e.g. /stage/finalize).
  - Browse a root to publish your files.
  - Enable/Disable auto-fix as needed.
  - Dry-run the publisher to validate your settings before publishing.
  - Publish your files.
  - Refresh History to see the published asset.
- Validate File:
  - Browse path for the file you want to validate.
  - Fill required fields for Asset Name and Version if used with the auto-fix feature.
  - Enable/Disable auto-fix as needed.
  - Click "Validate" to run.
  - Click "Open Fixed File in Houdini" to open the fixed file in Houdini.

---

## Next Steps:

1. Further Testing, validation improvements.
2. Proper Documentation and README.
