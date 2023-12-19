/*
Template app
*/
#ifdef _MSC_VER
    #include <winbase.h>
#else
    #include <cstring>
    #include <errno.h>
    #include <stdlib.h>
#endif

#include <iostream>
#include <sstream>
#include <string>
#include <vector>

constexpr char SCRIPT_NAME[] = "@@SCRIPT@@";
constexpr char PYTHON_VER[] = "@@PYTHON@@";

#ifdef DIAMOND_LOGGING
    #define LOG(x) std::cout << x
#else
    #define LOG(x)
#endif

#ifdef _MSC_VER
/*
    Windows
*/
void create_env()
{
}

#else
/*
 Unix
*/
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

void exec(const std::string& program)
{
    std::system(program.c_str());
}
#endif

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

    // TODO handle other args
    std::vector<char> buffer;

    std::stringstream ss;
    ss << installDir << "/venv/stdlib";
    if(!write_env("PYTHONHOME", ss.str()))
    {
        return -1;
    }

    ss = std::stringstream();
    ss << installDir << "/venv/lib/" << PYTHON_VER << "/site-packages";
    if(!write_env("PYTHONPATH", ss.str()))
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

    // Exec the program
    ss = std::stringstream();
    ss << installDir
#ifdef _MSC_VER
       << "/venv/Scripts/python.exe"
#else
       << "/venv/bin/python"
#endif
       << " -m " << SCRIPT_NAME;

    for(int i = 1; i < argc; ++i)
    {
        ss << " " << argv[i];
    }

    exec(ss.str());

    return 0;
}