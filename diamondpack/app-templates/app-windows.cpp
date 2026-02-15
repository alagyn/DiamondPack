/*
Template app
*/

#define WIN32_LEAN_AND_MEAN

#include <Windows.h>
#include <strsafe.h>
#include <winbase.h>

#ifdef GUI_APP
    #include <shellapi.h>
#endif

// Use backslashes
#define SEP L"\\"

#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#ifdef DIAMOND_LOGGING
    #define LOG(x) std::wcout << "<> " << x
#else
    #define LOG(x)
#endif

void showError(const wchar_t* from)
{
    // Display the error message and exit the process
    wchar_t* msgBuff;
    DWORD dw = GetLastError();

    FormatMessageW(
        FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM
            | FORMAT_MESSAGE_IGNORE_INSERTS,
        NULL,
        dw,
        MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        (wchar_t*)&msgBuff,
        0,
        NULL
    );

    int size = lstrlenW(msgBuff) + lstrlenW(from) + 40;

    wchar_t* displayBuff = new wchar_t[size];

    StringCchPrintfW(displayBuff, size, L"Error: %s: %s", from, msgBuff);

    std::wcout << L"Error: " << from << L", " << msgBuff << std::endl;
    MessageBoxW(NULL, (LPCWSTR)displayBuff, L"Error", MB_OK);

    LocalFree(msgBuff);
}

bool write_env(const wchar_t* name, const std::wstring& value)
{
    LOG(L"Setting " << name << L"=" << value << std::endl);
    if(!SetEnvironmentVariableW(name, value.c_str()))
    {
        showError(L"diamondpack:write_env()");
        return false;
    }
    return true;
}

std::wstring get_env(const wchar_t* name)
{
    wchar_t buffer[1024];
    if(!GetEnvironmentVariableW(name, buffer, 1024))
    {
        showError(L"diamondpack:get_env()");
        exit(1);
    }

    return std::wstring(buffer);
}

#ifdef GUI_APP
int WINAPI
WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, PSTR lpCmdLine, int nCmdShow)
#else
int wmain(int argc, wchar_t** argv)
#endif
{
    // First we parse out the home directory of this application
#ifdef GUI_APP
    int argc;
    wchar_t** argv = CommandLineToArgvW(GetCommandLineW(), &argc);
#endif
    wchar_t* appPath = argv[0];
    int lastSlash = 0;
    for(int i = 0; appPath[i] != 0; ++i)
    {
        if(appPath[i] == L'/' || appPath[i] == L'\\')
        {
            lastSlash = i;
        }
    }

    std::wstring installDir(appPath, lastSlash);

    // Fallback if we get empty wstring
    if(installDir.empty())
    {
        installDir = std::filesystem::current_path().wstring();
    }

    LOG(L"App location: " << installDir << std::endl);

    // Set up the PYTHONHOME var
    std::wstringstream ss;
    ss << installDir << SEP L"venv";
    if(!write_env(L"PYTHONHOME", ss.str()))
    {
        return -1;
    }

    ss = std::wstringstream();
    ss << installDir << L"/venv/Lib;" << get_env(L"PATH") << L';';
    if(!write_env(L"PATH", ss.str()))
    {
        return -1;
    }

    // Set up exec wstring
    ss = std::wstringstream();
    /*
        Windows is wack, so we have to double quote this otherwise it gets
       stripped
    */
    ss << L"\"" << installDir
       << SEP L"venv" SEP L"Scripts" SEP
#ifdef GUI_APP
              L"pythonw.exe"
#else
              L"python.exe"
#endif
              L"\" @@COMMAND@@ ";

    // Add all remaining cmd line args
    for(int i = 1; i < argc; ++i)
    {
        ss << L" " << argv[i];
    }

    // Exec the app
    STARTUPINFOW si;
    PROCESS_INFORMATION pi;

    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    std::wstring cmdline = ss.str();

    LOG(L"Executing: " << ss.str() << std::endl);
    bool procCreated = CreateProcessW(
        NULL,                    // No module name (use command line)
        (LPWSTR)cmdline.c_str(), // Command line
        NULL,                    // Process handle not inheritable
        NULL,                    // Thread handle not inheritable
        FALSE,                   // Set handle inheritance to FALSE
        0,                       // No creation flags
        NULL,                    // Use parent's environment block
        NULL,                    // Use parent's starting directory
        &si,                     // Pointer to STARTUPINFO structure
        &pi                      // Pointer to PROCESS_INFORMATION structure
    );

    if(!procCreated)
    {
        LOG(L"Failed to start process");
        showError(L"diamondpack:create_process()");
    }

    // Wait until child process exits.
    WaitForSingleObject(pi.hProcess, INFINITE);

    DWORD out;

    GetExitCodeProcess(pi.hProcess, &out);

    // Close process and thread handles.
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    LOG(L"Return Code: " << out << std::endl);
    return out;
}