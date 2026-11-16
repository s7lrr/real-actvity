#define MyAppName "Presence Studio"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Presence Studio"
#define MyAppExeName "PresenceStudio.exe"

[Setup]
AppId={{6B6DBE22-57E0-4A9E-8C83-2EAB29D26D12}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Presence Studio
DefaultGroupName={#MyAppName}
OutputDir=..\..\installer
OutputBaseFilename=PresenceStudio-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "..\dist\PresenceStudio.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Presence Studio"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Presence Studio"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Presence Studio"; Flags: postinstall nowait skipifsilent
