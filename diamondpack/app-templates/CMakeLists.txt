cmake_minimum_required(VERSION 3.26)

project(diamondpack-app)

if(NOT EXEC_NAME)
    message(FATAL "EXEC_NAME not set")
endif()

add_executable(${EXEC_NAME}
    app.cpp
)

