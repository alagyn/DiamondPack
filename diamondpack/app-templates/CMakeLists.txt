cmake_minimum_required(VERSION 3.24)

project(diamondpack-app)

if(NOT EXEC_NAME)
    message(FATAL "EXEC_NAME not set")
endif()

option(DEBUG_LOGS "Enable Debug Logging in app" OFF)
option(IS_GUI "Enable GUI mode for windows" OFF)

set(CMAKE_CXX_STANDARD 17)

# template cpp file is always renamed to app.cpp

if(NOT MSVC)
    add_executable(${EXEC_NAME}
        app.cpp
    )
else()
    if(IS_GUI)
        add_executable(${EXEC_NAME} WIN32
            app.cpp
        )
        target_compile_definitions(${EXEC_NAME}
            PUBLIC
                GUI_APP=1
        )
    else()
        add_executable(${EXEC_NAME}
            app.cpp
        )
    endif()

endif()

if(${DEBUG_LOGS})
    target_compile_definitions(${EXEC_NAME} PRIVATE DIAMOND_LOGGING)
endif()
