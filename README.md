# Presence Studio

Presence Studio is a Windows desktop application for configuring Discord Rich Presence through the official local Discord RPC connection.

## Features

- Configure Playing, Watching, Listening, and Competing activities.
- Set activity details and state text.
- Select a local image for the application's preview.
- Configure large and small Discord application asset keys.
- Add an optional activity button.
- Save settings locally on the current Windows account.
- Apply or clear the activity from the desktop application.

## Requirements

- Windows 10 or Windows 11, 64-bit.
- The Discord desktop application must be running.
- A Discord Application ID created by the application owner.
- The image asset keys must already exist in the Discord Developer Portal.

The packaged Windows installer includes the Python runtime and required libraries. End users do not need to install Python, PySide6, or pypresence.

## Installation

Download `PresenceStudio-Setup.exe` from the latest GitHub Release and run the installer.

If you are building the application yourself:

1. Install Python 3.11 or newer on the build computer.
2. Run `build.bat`.
3. The standalone executable will be created at `dist/PresenceStudio.exe`.
4. To create a Windows setup installer, compile `PresenceStudio.iss` with Inno Setup after building the executable.

## First launch

1. Start the Discord desktop application and sign in.
2. Open Presence Studio.
3. Enter your Discord Application ID.
4. Select an activity type.
5. Enter the activity title and description.
6. Upload your image as an Application Asset in the Developer Portal.
7. Enter the exact asset key in the `Discord asset key` field.
8. Select `Apply Rich Presence`.

## Images

A local image selected in Presence Studio is used only for the preview inside the application. Discord clients cannot read a local file path from your computer. To display an image to other Discord users, upload it to your Discord application's Rich Presence Assets and enter its exact asset key.

## Activity types

The application supports the activity types exposed by Discord Rich Presence RPC:

- Playing
- Watching
- Listening
- Competing

Streaming and Custom Status are not supported by this RPC integration.

## Examples

### Example 1

Add your first screenshot below.

![Example 1](docs/examples/example-1.png)

### Example 2

Add your second screenshot below.

![Example 2](docs/examples/example-2.png)

## Build from source

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

For a standalone executable:

```powershell
build.bat
```

## GitHub Actions

The workflow in `.github/workflows/build-windows.yml` builds the standalone executable and Windows setup installer on GitHub's Windows runner. Push a version tag such as `v1.1.0` to trigger a Release build.

## Data and privacy

Settings are stored locally in:

```text
%APPDATA%\PresenceStudio\settings.json
```

The application does not ask for, read, or store a Discord user token or account password.

## Troubleshooting

- **Discord is not detected:** Make sure the Discord desktop application is open. The browser version is not sufficient for local RPC.
- **Invalid Application ID:** Copy the numeric Application ID from the General Information page of your Discord application.
- **Image is not visible to other users:** Confirm that the image is uploaded as an application asset and that the asset key matches exactly.
- **Activity does not appear:** Check that Discord desktop is running and that the selected application has been configured correctly.

## License

Choose and add a license before publishing this repository publicly.
