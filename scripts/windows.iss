; Build with build_installer.py. No administrator or global Python changes.
[Setup]
AppId={{A62F8529-C5B2-427A-B471-51689694BB48}
AppName=SceneScout
AppVersion={#AppVersion}
AppPublisher=Fatih Haslak
AppPublisherURL=https://github.com/Fatih-Haslak/scenescout
AppSupportURL=https://github.com/Fatih-Haslak/scenescout/issues
AppUpdatesURL=https://github.com/Fatih-Haslak/scenescout/releases/latest
DefaultDirName={localappdata}\Programs\SceneScout
DefaultGroupName=SceneScout
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
WizardStyle=modern
DisableWelcomePage=no
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=SceneScout-Setup-Windows-x64
Compression=lzma2
SolidCompression=yes
LicenseFile={#StageDir}\LICENSE
UninstallDisplayName=SceneScout
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Languages]
Name: english; MessagesFile: "compiler:Default.isl"
Name: turkish; MessagesFile: "compiler:Languages\Turkish.isl"

[CustomMessages]
english.PrepareNote=SceneScout searches video scenes locally.%n%nNo manual Python installation is needed. On first launch, internet is required to prepare Python and dependencies. The first video downloads approximately 1.5 GB of model weights. Leave several GB of free disk space.%n%nKeep the launch window open while using the app. Your video library is stored separately and is preserved during updates and uninstall.
turkish.PrepareNote=SceneScout, videolardaki sahneleri bilgisayarınızda arar.%n%nElle Python kurmanız gerekmez. İlk açılışta Python ve gerekli paketler internetten hazırlanır. İlk video için yaklaşık 1,5 GB model indirilir. Diskte birkaç GB boş alan bırakın.%n%nUygulamayı kullanırken açılış penceresini açık tutun. Video arşiviniz ayrı saklanır; güncelleme ve kaldırma sırasında korunur.
english.OpenGuide=Open the getting started guide
turkish.OpenGuide=Başlangıç rehberini aç
english.Launch=Launch SceneScout (first launch needs internet)
turkish.Launch=SceneScout'u başlat (ilk açılış internet gerektirir)
english.Guide=Getting started
turkish.Guide=Başlangıç rehberi
english.GPU=SceneScout - NVIDIA GPU (optional)
turkish.GPU=SceneScout - NVIDIA GPU (isteğe bağlı)

[Tasks]
Name: desktopicon; Description: "{cm:CreateDesktopIcon}"

[Files]
Source: "{#StageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userdesktop}\SceneScout"; Filename: "{app}\Start.cmd"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{group}\SceneScout"; Filename: "{app}\Start.cmd"; WorkingDir: "{app}"
Name: "{group}\{cm:GPU}"; Filename: "{app}\Start-GPU.cmd"; WorkingDir: "{app}"
Name: "{group}\{cm:Guide}"; Filename: "{app}\QUICKSTART.html"
Name: "{group}\{cm:UninstallProgram,SceneScout}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\QUICKSTART.html"; Description: "{cm:OpenGuide}"; Flags: shellexec nowait postinstall skipifsilent unchecked
Filename: "{app}\Start.cmd"; WorkingDir: "{app}"; Description: "{cm:Launch}"; Flags: shellexec nowait postinstall skipifsilent

[UninstallDelete]
; Only remove generated Python bytecode; never remove the separate user library.
Type: files; Name: "{app}\src\scenescout\__pycache__\*.pyc"
Type: dirifempty; Name: "{app}\src\scenescout\__pycache__"

[Code]
procedure InitializeWizard;
begin
  CreateOutputMsgPage(wpWelcome, 'SceneScout', ExpandConstant('{cm:Guide}'), ExpandConstant('{cm:PrepareNote}'));
end;
