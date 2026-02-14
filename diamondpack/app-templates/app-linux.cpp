/*
Template app
*/

#include <cstring>
#include <errno.h>
#include <stdlib.h>

// Use forward slashes
#define SEP "/"

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
    int err = setenv(name, value.c_str(), 1);
    if(err != 0)
    {
        LOG("Error setting '" << name << "=" << value << "'\n");
        LOG(strerror(errno) << "\n");
        return false;
    }
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

    ss = std::stringstream();
    ss << installDir << "/venv/bin";
    if(!write_env("LD_LIBRARY_PATH", ss.str()))
    {
        return -1;
    }

    // Set up exec string
    ss = std::stringstream();
    ss << "\"" << installDir
       << "/venv/bin/python"
          "\" @@COMMAND@@ ";

    // Add all remaining cmd line args
    for(int i = 1; i < argc; ++i)
    {
        ss << " " << argv[i];
    }

    // Exec the app
    LOG("Executing: " << ss.str() << std::endl);
    int out = std::system(ss.str().c_str());
    LOG("Return Code: " << out << std::endl);
    return out;
}