/*
Template app
*/
#ifdef _MSC_VER
    #define WIN32_LEAN_AND_MEAN

    #include <Windows.h>
    #include <strsafe.h>
    #include <winbase.h>

    // Use backslashes
    #define SEP "\\"
#else
    #include <cstring>
    #include <errno.h>
    #include <stdlib.h>

    // Use forward slashes
    #define SEP "/"
#endif

#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#ifdef DIAMOND_LOGGING
    #define LOG(x) std::cout << "<> " << x
#else
    #define LOG(x)
#endif

bool write_env(const char* name, const std::string& value)
{
    LOG("Setting " << name << "=" << value << std::endl);
#ifdef _MSC_VER
    if(!SetEnvironmentVariableA(name, value.c_str()))
    {
        // Display the error message and exit the process
        char* msgBuff;
        DWORD dw = GetLastError();

        FormatMessageA(
            FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM
                | FORMAT_MESSAGE_IGNORE_INSERTS,
            NULL,
            dw,
            MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
            (char*)&msgBuff,
            0,
            NULL
        );

        const char* from = "Set ENV";
        size_t size = lstrlenA(msgBuff) + lstrlenA(from) + 40;

        char* displayBuff = new char[size];

        StringCchPrintfA(displayBuff, size, "Error: %s: %s", from, msgBuff);

        std::wcout << L"Error: " << from << L", " << msgBuff << std::endl;
        MessageBoxA(NULL, (LPCSTR)displayBuff, "Error", MB_OK);

        LocalFree(msgBuff);
    }
#else
    int err = setenv(name, value.c_str(), 1);
    if(err != 0)
    {
        LOG("Error setting '" << name << "=" << value << "'\n");
        LOG(strerror(errno) << "\n");
        return false;
    }
#endif
    return true;
}

int main(int argc, char** argv)
{
    // First we parse out the home directory of this application
    char* appPath = argv[0];
    int lastSlash = 0;
    for(int i = 0; appPath[i] != 0; ++i)
    {
        if(appPath[i] == '/' || appPath[i] == '\\')
        {
            lastSlash = i;
        }
    }

    std::string installDir(appPath, lastSlash);

    // Fallback if we get empty string
    if(installDir.empty())
    {
        installDir = std::filesystem::current_path().string();
    }

    LOG("App location: " << installDir << std::endl);

    // Set up the PYTHONHOME var
    std::stringstream ss;
    ss << installDir << SEP "venv";
    if(!write_env("PYTHONHOME", ss.str()))
    {
        return -1;
    }

#ifndef _MSC_VER
    ss = std::stringstream();
    ss << installDir << "/venv/bin";
    if(!write_env("LD_LIBRARY_PATH", ss.str()))
    {
        return -1;
    }
#endif

    // Set up exec string
    ss = std::stringstream();
    ss << "\""
#ifdef _MSC_VER
       /*
           Windows is wack, so we have to double quote this otherwise it gets
          stripped
       */
       << "\""
#endif
       << installDir

#ifdef _MSC_VER
       << SEP "venv" SEP "Scripts" SEP "python.exe"
#else
       << "/venv/bin/python"
#endif
              "\" @@COMMAND@@ "

#ifdef _MSC_VER
              //Close for the double quote
              "\""
#endif
        ;

    // Add all remaining cmd line args
    for(int i = 1; i < argc; ++i)
    {
        ss << " " << argv[i];
    }

    // Exec the app
    // TODO change windows to use CreateProcess?
    LOG("Executing: " << ss.str() << std::endl);
    int out = std::system(ss.str().c_str());
    LOG("Return Code: " << out << std::endl);
    return out;
}