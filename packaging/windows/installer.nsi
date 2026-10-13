; PastyNew Password Generator - NSIS installer script
;
; Build on Windows:
;     makensis -DpastypwExe="..\..\dist\pastypw.exe" packaging\windows\installer.nsi
;
; Produces: dist\PastyNew-PasswordGenerator-Setup-<version>.exe
;
!ifndef pastypwExe
  !define pastypwExe "..\..\dist\pastypw.exe"
!endif

!define appName "PastyNew Password Generator"
!define appShort "pastypw"
!define appPublisher "PastyNew"
!define appVersion "1.0.0"
!define appURL "https://github.com/PastyNew/pastypw"
!define appExeName "pastypw.exe"
!define appIconFile "..\..\build\icons\pastypw.ico"
!define uninstallKey "Software\Microsoft\Windows\CurrentVersion\Uninstall\${appShort}"

Name "${appName}"
OutFile "..\..\dist\PastyNew-PasswordGenerator-Setup-${appVersion}.exe"
InstallDir "$PROGRAMFILES64\PastyNew Password Generator"
InstallDirRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${appShort}" "InstallLocation"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

VIProductVersion "${appVersion}.0"
VIAddVersionKey "ProductName" "${appName}"
VIAddVersionKey "CompanyName" "${appPublisher}"
VIAddVersionKey "FileDescription" "${appName}"
VIAddVersionKey "FileVersion" "${appVersion}"
VIAddVersionKey "ProductVersion" "${appVersion}"
VIAddVersionKey "LegalCopyright" "(c) 2026 ${appPublisher}"

!include "MUI2.nsh"
!include "FileFunc.nsh"

!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${appExeName}"
!define MUI_FINISHPAGE_RUN_TEXT "Запустить / Launch"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Russian"
!insertmacro MUI_LANGUAGE "English"

Section "Install" SEC_APP
  SectionIn RO
  SetOutPath "$INSTDIR"
  File "${pastypwExe}"

  IfFileExists "$INSTDIR\${appExeName}" 0 +2
    Delete "$INSTDIR\${appExeName}"
  File "${pastypwExe}"

  ; start menu + desktop shortcuts
  CreateDirectory "$SMPROGRAMS\PastyNew"
  CreateShortcut "$SMPROGRAMS\PastyNew\${appName}.lnk" "$INSTDIR\${appExeName}"
  CreateShortcut "$SMPROGRAMS\PastyNew\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  CreateShortcut "$DESKTOP\${appName}.lnk" "$INSTDIR\${appExeName}"

  ; registry (uninstall information + autostart-free app id)
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${appShort}" \
    "DisplayName" "${appName}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${appShort}" \
    "DisplayVersion" "${appVersion}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${appShort}" \
    "Publisher" "${appPublisher}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${appShort}" \
    "URLInfoAbout" "${appURL}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${appShort}" \
    "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${appShort}" \
    "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${appShort}" \
    "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${appShort}" \
    "NoRepair" 1

  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\${appExeName}"
  Delete "$INSTDIR\uninstall.exe"
  RMDir "$INSTDIR"
  RMDir /r "$APPDATA\PastyNew Password Generator"

  Delete "$SMPROGRAMS\PastyNew\${appName}.lnk"
  Delete "$SMPROGRAMS\PastyNew\Uninstall.lnk"
  RMDir "$SMPROGRAMS\PastyNew"
  Delete "$DESKTOP\${appName}.lnk"

  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${appShort}"
  DeleteRegKey HKLM "Software\PastyNew"
SectionEnd

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SEC_APP} "$(^Name)"
!insertmacro MUI_FUNCTION_DESCRIPTION_END