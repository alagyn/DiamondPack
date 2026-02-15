cmake_minimum_required(VERSION 3.24)

project(diamondpack-app)

if(NOT EXEC_NAME)
    message(FATAL_ERROR "EXEC_NAME not set")
endif()

option(DEBUG_LOGS "Enable Debug Logging in app" OFF)
option(GUI_APP "Enable GUI mode for windows" OFF)
option(HAS_ICON "Enable the exec icon for windows" OFF)

set(CMAKE_CXX_STANDARD 17)

# template cpp file is always renamed to app.cpp

if(HAS_ICON)
    # add rc file which contains manifest that points at app.ico
    set(RC_FILE app.rc)
else()
    unset(RC_FILE)
endif()


if(NOT MSVC)
    add_executable(${EXEC_NAME}
        app.cpp
        ${RC_FILE}
    )
else()
    if(GUI_APP)
        # build app as win32 to disable opening a console
        set(APP_TYPE WIN32)
    else()
        unset(APP_TYPE)
    endif()

    add_executable(${EXEC_NAME} ${APP_TYPE}
        app.cpp
        ${RC_FILE}
    )

    if(GUI_APP)
        target_compile_definitions(${EXEC_NAME}
            PRIVATE
                GUI_APP=1
        )
    endif()
endif()

if(${DEBUG_LOGS})
    target_compile_definitions(${EXEC_NAME} PRIVATE DIAMOND_LOGGING)
endif()
