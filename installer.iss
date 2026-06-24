; ArchForge Pro — Inno Setup Script
; Compile this with Inno Setup 6: https://jrsoftware.org/isinfo.php

[Setup]
AppName=ArchForge Pro
AppVersion=1.0.0
AppPublisher=ArchForge
AppPublisherURL=https://github.com
AppSupportURL=https://github.com
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
DefaultDirName={autopf}\ArchForgePro
DefaultGroupName=ArchForge Pro
AllowNoIcons=yes
LicenseFile=
OutputDir=dist\installer
OutputBaseFilename=ArchForgePro_Setup_v1.0.0
SetupIconFile=app\resources\images\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableDirPage=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\ArchForgePro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ArchForge Pro"; Filename: "{app}\ArchForgePro.exe"
Name: "{group}\Uninstall ArchForge Pro"; Filename: "{uninstallexe}"
Name: "{autodesktop}\ArchForge Pro"; Filename: "{app}\ArchForgePro.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ArchForgePro.exe"; Description: "Launch ArchForge Pro"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove the database and ML models the user created
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\ml_models"
