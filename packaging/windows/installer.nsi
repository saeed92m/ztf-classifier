Unicode true

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"

; Resolve all build inputs and outputs from the repository root.
!cd "..\.."

!define PRODUCT_NAME "ZTF Classifier"
!define PRODUCT_VERSION "0.1.0-preview.1"
!define PRODUCT_PUBLISHER "Pishgaman Novandish Fanavargostar Keyhan"
!define WEBVIEW2_CLIENT_ID "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"

Name "${PRODUCT_NAME}"
OutFile "dist\ZTFClassifier-0.1.0-preview.1-Setup.exe"
Icon "src\ztf_classifier\web\static\ztf-logo.ico"
InstallDir "$LOCALAPPDATA\Programs\ZTFClassifier"
InstallDirRegKey HKCU "Software\ZTFClassifier" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
ShowInstDetails show
ShowUninstDetails show

VIProductVersion "0.1.0.1"
VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey "ProductVersion" "${PRODUCT_VERSION}"
VIAddVersionKey "FileDescription" "ZTF Classifier Windows experimental desktop"
VIAddVersionKey "CompanyName" "${PRODUCT_PUBLISHER}"
VIAddVersionKey "Comments" "Experimental Park evaluation pre-release; not a scientific production release."

!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\ZTFClassifier.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ZTF Classifier"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

LangString WebView2InstallFailed ${LANG_ENGLISH} "Automatic Microsoft Edge WebView2 Runtime installation failed (exit code: $1). Check the internet connection and install the Runtime from the official Microsoft website."

; WebView2 is mandatory. If it is absent, open Microsoft's official download page and abort.
; Do not continue with a partially installed desktop application.
Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "This experimental preview requires 64-bit Windows."
    Abort
  ${EndIf}
  SetShellVarContext current
  SetRegView 64
  ClearErrors
  ReadRegStr $0 HKLM "SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\${WEBVIEW2_CLIENT_ID}" "pv"
  ${If} $0 == ""
  ${OrIf} $0 == "0.0.0.0"
    ReadRegStr $0 HKCU "Software\Microsoft\EdgeUpdate\Clients\${WEBVIEW2_CLIENT_ID}" "pv"
  ${EndIf}
  ${If} $0 == ""
  ${OrIf} $0 == "0.0.0.0"
    DetailPrint "Installing Microsoft Edge WebView2 Runtime..."
    SetOutPath "$TEMP"
    ; Resolve the staged bootstrapper from the installer source directory.
    File /oname=MicrosoftEdgeWebView2Setup.exe "packaging\windows\MicrosoftEdgeWebView2Setup.exe"
    ExecWait '"$TEMP\MicrosoftEdgeWebView2Setup.exe" /silent /install' $1
    Delete "$TEMP\MicrosoftEdgeWebView2Setup.exe"
    ClearErrors
    ReadRegStr $0 HKLM "SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\${WEBVIEW2_CLIENT_ID}" "pv"
    ${If} $0 == ""
    ${OrIf} $0 == "0.0.0.0"
      ReadRegStr $0 HKCU "Software\Microsoft\EdgeUpdate\Clients\${WEBVIEW2_CLIENT_ID}" "pv"
    ${EndIf}
    ${If} $0 == ""
    ${OrIf} $0 == "0.0.0.0"
      MessageBox MB_ICONSTOP "$(WebView2InstallFailed)"
      Abort
    ${EndIf}
  ${EndIf}
FunctionEnd

Section "Application" SEC_APPLICATION
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File /r "dist\ZTFClassifier\*.*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  CreateDirectory "$SMPROGRAMS\ZTF Classifier"
  CreateShortcut "$SMPROGRAMS\ZTF Classifier\ZTF Classifier.lnk" "$INSTDIR\ZTFClassifier.exe"
  CreateShortcut "$DESKTOP\ZTF Classifier.lnk" "$INSTDIR\ZTFClassifier.exe"

  WriteRegStr HKCU "Software\ZTFClassifier" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ZTFClassifier" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ZTFClassifier" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ZTFClassifier" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ZTFClassifier" "Comments" "Experimental Park evaluation pre-release; not a scientific production release."
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ZTFClassifier" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ZTFClassifier" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ZTFClassifier" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ZTFClassifier" "NoRepair" 1
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  Delete "$SMPROGRAMS\ZTF Classifier\ZTF Classifier.lnk"
  RMDir "$SMPROGRAMS\ZTF Classifier"
  Delete "$DESKTOP\ZTF Classifier.lnk"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ZTFClassifier"
  DeleteRegKey HKCU "Software\ZTFClassifier"
  RMDir /r "$INSTDIR"
  ; Preserve %LOCALAPPDATA%\ZTFClassifier user data, projects, logs and exports.
SectionEnd
