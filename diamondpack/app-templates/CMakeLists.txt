cmake_minimum_required(VERSION 3.24)

project(diamondpack-app)

if(NOT EXEC_NAME)
    message(FATAL "EXEC_NAME not set")
endif()

set(CMAKE_CXX_STANDARD 17)

add_executable(${EXEC_NAME}
    app.cpp
)

target_link_libraries(${EXEC_NAME} -static)
