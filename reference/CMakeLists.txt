cmake_minimum_required(VERSION 3.16)
project(vrref_reference CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# GLOBBED ON PURPOSE. Listing the files by hand is how tests/test_depth_slice.cpp came to be
# written, committed, and never compiled -- the suite reported "all passed" with a whole file
# missing. CONFIGURE_DEPENDS makes the build re-glob when the directory changes.
file(GLOB VRREF_TEST_SOURCES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/tests/*.cpp")
add_executable(vrref_tests ${VRREF_TEST_SOURCES})

target_include_directories(vrref_tests PRIVATE include)

if(MSVC)
    target_compile_options(vrref_tests PRIVATE /W4 /permissive-)
else()
    target_compile_options(vrref_tests PRIVATE -Wall -Wextra)
    find_package(Threads REQUIRED)
    target_link_libraries(vrref_tests PRIVATE Threads::Threads)
endif()

enable_testing()
add_test(NAME reference_maths COMMAND vrref_tests)
