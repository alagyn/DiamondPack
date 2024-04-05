cmake_minimum_required(VERSION 3.24)

project(diamondpack-app)

if(NOT EXEC_NAME)
    message(FATAL "EXEC_NAME not set")
endif()

option(DEBUG_LOGS "Enable Debug Logging in app" OFF)

set(CMAKE_CXX_STANDARD 17)

add_executable(${EXEC_NAME}
    app.cpp
)

if(${DEBUG_LOGS})
    target_compile_definitions(${EXEC_NAME} PRIVATE DIAMOND_LOGGING)
endif()
