; ============================================================================
;  Skrip Inno Setup - Program Pembukuan Kantin Koperasi
;  Menghasilkan: installer_output\KantinKoperasi_Setup_1.0.0.exe
;  Cara pakai  : jalankan build_installer.bat (atau buka berkas ini di Inno Setup)
; ============================================================================

#define NamaApp        "Program Pembukuan Kantin Koperasi"
#define VersiApp       "2.0.0"
#define PenerbitApp    "Pembukuan Kantin Koperasi"
#define ExeApp         "KantinKoperasi.exe"

[Setup]
AppId={{8F3C2A57-4B19-4D6E-9C81-0A7E5D2B6C44}
AppName={#NamaApp}
AppVersion={#VersiApp}
AppVerName={#NamaApp} {#VersiApp}
AppPublisher={#PenerbitApp}
DefaultDirName={autopf}\KantinKoperasi
DefaultGroupName=Pembukuan Kantin Koperasi
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=KantinKoperasi_Setup_{#VersiApp}
SetupIconFile=assets\ikon.ico
UninstallDisplayIcon={app}\{#ExeApp}
UninstallDisplayName={#NamaApp}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=LISENSI.txt
InfoBeforeFile=

[Languages]
Name: "indonesia"; MessagesFile: "compiler:Default.isl"

[Messages]
indonesia.WelcomeLabel1=Selamat datang di pemasangan [name]
indonesia.WelcomeLabel2=Program ini akan memasang [name/ver] pada komputer Anda.%n%nDisarankan menutup aplikasi lain sebelum melanjutkan.%n%nData pembukuan disimpan terpisah dari program, sehingga tetap aman walaupun program diperbarui atau dihapus.
indonesia.FinishedLabel=Pemasangan [name] selesai. Program dapat dibuka melalui ikon di Desktop atau menu Start.

[Tasks]
Name: "desktopicon"; Description: "Buat ikon di Desktop"; GroupDescription: "Pintasan tambahan:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "Buat ikon di Taskbar (Quick Launch)"; GroupDescription: "Pintasan tambahan:"; Flags: unchecked

[Files]
Source: "dist\{#ExeApp}";  DestDir: "{app}"; Flags: ignoreversion
Source: "PANDUAN.md";      DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "README.md";       DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "LISENSI.txt";     DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "assets\ikon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "contoh\*";        DestDir: "{app}\contoh"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\{#NamaApp}";            Filename: "{app}\{#ExeApp}"; IconFilename: "{app}\assets\ikon.ico"
Name: "{group}\Panduan Pemakaian";     Filename: "{app}\PANDUAN.md"
Name: "{group}\Hapus {#NamaApp}";      Filename: "{uninstallexe}"
Name: "{autodesktop}\Pembukuan Kantin"; Filename: "{app}\{#ExeApp}"; IconFilename: "{app}\assets\ikon.ico"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Pembukuan Kantin"; Filename: "{app}\{#ExeApp}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#ExeApp}"; Description: "Jalankan {#NamaApp} sekarang"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\assets"
Type: filesandordirs; Name: "{app}\contoh"

[Code]
// Ingatkan bahwa data pembukuan TIDAK ikut terhapus saat uninstall.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  FolderData: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    FolderData := ExpandConstant('{localappdata}\KantinKoperasi');
    if DirExists(FolderData) then
      MsgBox('Program sudah dihapus.' + #13#10 + #13#10 +
             'Data pembukuan Anda TIDAK ikut terhapus dan masih tersimpan di:' + #13#10 +
             FolderData + #13#10 + #13#10 +
             'Hapus folder tersebut secara manual bila memang tidak diperlukan lagi.',
             mbInformation, MB_OK);
  end;
end;
