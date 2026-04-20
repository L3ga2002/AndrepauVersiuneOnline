' ========================================================
' ANDREPAU POS - Launcher Ascuns (fara ferestre CMD)
' Porneste MongoDB + Backend + Bridge fara a afisa CMD-uri
' Deschide browserul in mod aplicatie
' ========================================================

Option Explicit

Dim oShell, oFso, sScriptDir, sAppDir, sBackendDir
Set oShell = CreateObject("WScript.Shell")
Set oFso = CreateObject("Scripting.FileSystemObject")

sScriptDir = oFso.GetParentFolderName(WScript.ScriptFullName)
sAppDir = sScriptDir
sBackendDir = sAppDir & "\backend"

' --- 1. Verifica daca backend-ul deja ruleaza (port 8001) ---
Dim bBackendRunning
bBackendRunning = False
On Error Resume Next
Dim oHttp
Set oHttp = CreateObject("MSXML2.XMLHTTP")
oHttp.Open "GET", "http://localhost:8001/api/seed", False
oHttp.setTimeoutTimes 1000, 1000, 1000, 1000
oHttp.Send
If Err.Number = 0 And oHttp.Status > 0 Then
    bBackendRunning = True
End If
On Error Goto 0

If bBackendRunning Then
    ' Aplicatia ruleaza deja - deschide doar browserul
    OpenBrowser
    WScript.Quit
End If

' --- 2. Porneste MongoDB (daca e serviciu, pornit deja; altfel lanseaza) ---
On Error Resume Next
oShell.Run "net start MongoDB", 0, False
On Error Goto 0

Dim sMongod
sMongod = ""
If oFso.FileExists("C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe") Then
    sMongod = "C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe"
ElseIf oFso.FileExists("C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe") Then
    sMongod = "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe"
ElseIf oFso.FileExists("C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe") Then
    sMongod = "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe"
End If

If sMongod <> "" Then
    If Not oFso.FolderExists("C:\data\db") Then
        oFso.CreateFolder "C:\data"
        oFso.CreateFolder "C:\data\db"
    End If
    ' Porneste mongod ASCUNS (0 = WindowStyle hidden)
    oShell.Run """" & sMongod & """ --dbpath ""C:\data\db""", 0, False
    WScript.Sleep 2000
End If

' --- 3. Porneste Backend FastAPI cu pythonw (fara consola) ---
' pythonw.exe ruleaza Python fara fereastra de consola
Dim sPythonw
sPythonw = FindPythonw()

If sPythonw = "" Then
    MsgBox "EROARE: Python (pythonw.exe) nu a fost gasit! Instalati Python de pe python.org", 48, "ANDREPAU POS"
    WScript.Quit 1
End If

' Comanda pentru backend - redirectionam output in log
Dim sBackendLog
sBackendLog = sAppDir & "\logs\backend.log"
EnsureLogsDir

Dim sBackendCmd
sBackendCmd = "cmd /c cd /d """ & sBackendDir & """ && """ & sPythonw & """ -m uvicorn server:app --host 0.0.0.0 --port 8001 > """ & sBackendLog & """ 2>&1"
oShell.Run sBackendCmd, 0, False

' --- 4. Porneste Bridge Fiscal cu pythonw (fara consola) ---
Dim sBridgeLog
sBridgeLog = sAppDir & "\logs\bridge.log"

Dim sBridgeCmd
sBridgeCmd = "cmd /c cd /d """ & sBackendDir & """ && """ & sPythonw & """ fiscal_bridge.py http://localhost:8001 > """ & sBridgeLog & """ 2>&1"
oShell.Run sBridgeCmd, 0, False

' --- 5. Asteapta ca backend-ul sa porneasca, apoi deschide browserul ---
WScript.Sleep 5000

' Poll backend pentru ready
Dim iRetry
For iRetry = 1 To 20
    On Error Resume Next
    Set oHttp = CreateObject("MSXML2.XMLHTTP")
    oHttp.Open "GET", "http://localhost:8001/api/sync/health", False
    oHttp.Send
    If Err.Number = 0 And oHttp.Status = 200 Then
        Exit For
    End If
    On Error Goto 0
    WScript.Sleep 1000
Next

OpenBrowser

' ========== FUNCTII ==========

Sub OpenBrowser
    ' Incearca Chrome in mod aplicatie (fara bara adresa), apoi Edge, apoi default
    Dim sChrome, sEdge
    sChrome = FindChrome()
    sEdge = FindEdge()

    If sChrome <> "" Then
        oShell.Run """" & sChrome & """ --app=http://localhost:8001 --disable-features=TranslateUI", 1, False
    ElseIf sEdge <> "" Then
        oShell.Run """" & sEdge & """ --app=http://localhost:8001", 1, False
    Else
        oShell.Run "http://localhost:8001", 1, False
    End If
End Sub

Function FindPythonw()
    Dim aPaths, sPath
    aPaths = Array( _
        "C:\Python312\pythonw.exe", _
        "C:\Python311\pythonw.exe", _
        "C:\Python310\pythonw.exe", _
        "C:\Python39\pythonw.exe", _
        "C:\Program Files\Python312\pythonw.exe", _
        "C:\Program Files\Python311\pythonw.exe", _
        "C:\Program Files\Python310\pythonw.exe" _
    )
    For Each sPath In aPaths
        If oFso.FileExists(sPath) Then
            FindPythonw = sPath
            Exit Function
        End If
    Next

    ' Incearca via PATH
    Dim sEnvPath, aDirs, sDir, sFull
    sEnvPath = oShell.ExpandEnvironmentStrings("%PATH%")
    aDirs = Split(sEnvPath, ";")
    For Each sDir In aDirs
        If sDir <> "" Then
            sFull = sDir
            If Right(sFull, 1) <> "\" Then sFull = sFull & "\"
            sFull = sFull & "pythonw.exe"
            If oFso.FileExists(sFull) Then
                FindPythonw = sFull
                Exit Function
            End If
        End If
    Next

    ' Fallback: python.exe (va afisa consola dar e mai bine decat nimic)
    Dim sPython
    sPython = ""
    For Each sPath In Array("C:\Python312\python.exe", "C:\Python311\python.exe", "C:\Python310\python.exe") 
        If oFso.FileExists(sPath) Then
            sPython = sPath
            Exit For
        End If
    Next
    FindPythonw = sPython
End Function

Function FindChrome()
    Dim aPaths, sPath
    aPaths = Array( _
        "C:\Program Files\Google\Chrome\Application\chrome.exe", _
        "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", _
        oShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Google\Chrome\Application\chrome.exe" _
    )
    For Each sPath In aPaths
        If oFso.FileExists(sPath) Then
            FindChrome = sPath
            Exit Function
        End If
    Next
    FindChrome = ""
End Function

Function FindEdge()
    Dim aPaths, sPath
    aPaths = Array( _
        "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", _
        "C:\Program Files\Microsoft\Edge\Application\msedge.exe" _
    )
    For Each sPath In aPaths
        If oFso.FileExists(sPath) Then
            FindEdge = sPath
            Exit Function
        End If
    Next
    FindEdge = ""
End Function

Sub EnsureLogsDir
    If Not oFso.FolderExists(sAppDir & "\logs") Then
        oFso.CreateFolder sAppDir & "\logs"
    End If
End Sub
