[Setup]
AppId={{B1B7A0F3-98D2-4E54-AF90-5C5C9F5A8120}
AppName=Presence Studio
AppVersion=1.1.0
AppPublisher=Presence Studio
DefaultDirName={autopf}\Presence Studio
DefaultGroupName=Presence Studio
OutputDir=installer
OutputBaseFilename=PresenceStudio-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\PresenceStudio.exe

[Files]
Source: "dist\PresenceStudio.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Presence Studio"; Filename: "{app}\PresenceStudio.exe"
Name: "{autodesktop}\Presence Studio"; Filename: "{app}\PresenceStudio.exe"

[Run]
Filename: "{app}\PresenceStudio.exe"; Description: "Launch Presence Studio"; Flags: postinstall nowait skipifsilent
