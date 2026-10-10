; Script de Inno Setup para crear el instalador de Windows de ElectroPredict.
; Requiere Inno Setup 6+ (https://jrsoftware.org/isinfo.php).
;
; Compilar con:
;     ISCC.exe empaquetado\instalador.iss
; (o abrir este archivo en el IDE de Inno Setup y pulsar Compilar)
;
; Antes de compilar, genere el ejecutable con empaquetado\build_exe.ps1,
; de modo que exista dist\ElectroPredict.exe.

#define AppName "ElectroPredict"
#define AppVersion "1.1.0"
#define AppPublisher "ElectroPredict"
#define AppExeName "ElectroPredict.exe"

[Setup]
AppId={{7B2C9E44-1A3F-4E7A-9C21-ELE7R0PRED1}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=ElectroPredict-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
; Permitir instalar sin privilegios de administrador (en el perfil del usuario).
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"
Name: "startmenuicon"; Description: "Crear un acceso directo en el Menu Inicio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\ejemplos\*"; DestDir: "{app}\ejemplos"; Flags: ignoreversion recursesubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startmenuicon
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"; Tasks: startmenuicon
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Iniciar {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Los modelos guardados por el usuario se conservan; solo se elimina lo instalado.
Type: filesandordirs; Name: "{app}\ejemplos"
