# BJI Logger Application

The BJI Logger Application is an user interface for the randomized clinical trial of knee braces for knee osteoarthritis (OA), Clinical Outcomes and costs associated with Rehabilitative interventions for Knee osteoarthritis (CORK).

The application is developed as part of the collaboration between the FHS MSK-IF and the Dr. T. Birmingham, Dr. D. Holdsworth and his team.

## Features
The application is built using Dash & Plotly and offers three features:

1. **Initialize Device**
    - Allows the user to initialize for a specified time an Arduino-based device that has been pre-programmed.

2. **Download Data**
    - Enables the user to download data collected from an Arduino-based device in either a .RAW or .CSV format.

3. **Data Analysis**
    - Provides a high-level summary of the collected data in a dashboard format.

## Building & Releasing

Windows and macOS builds are produced automatically by GitHub Actions
(`.github/workflows/build.yml`). PyInstaller cannot cross-compile, so each
binary is built on its own native runner (`windows-latest` / `macos-latest`)
in parallel.

**To test a build without releasing:** go to the **Actions** tab → *Build
desktop app* → **Run workflow**. When it finishes, the Windows and macOS zips
are downloadable from that run's *Artifacts* section (kept 30 days).

**To publish a release for end users:** push a version tag. The same build then
attaches the binaries to a public GitHub Release:

```bash
git tag v3.1
git push origin v3.1
```

**To build locally instead** (only produces a binary for your current OS):

```bash
pip install -r requirements.txt pyinstaller
pyinstaller index.spec --noconfirm
# output is in dist/BJI_Logger/
```

> Note: the produced `.exe`/`.app` are unsigned. Windows SmartScreen will warn
> on first launch, and macOS Gatekeeper will block the app until you approve it
> (right-click → Open, or *System Settings → Privacy & Security*). Proper code
> signing/notarization requires paid developer certificates and is a separate
> setup step.

## Credits
This application is based on the PySimpleGUI version of the application developed by Steve Pollmann.

