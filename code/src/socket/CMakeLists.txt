cmake_minimum_required(VERSION 3.11.0 FATAL_ERROR)

add_library(
  socket OBJECT
    socket.h
    socket.cpp
)

target_compile_options(
  socket
    PRIVATE
      ${_subco_compiler_warning_flags} -Wno-write-strings -Wno-class-memaccess 
)

target_include_directories(
  socket
    PUBLIC
      $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
      ${RAPIDJSON_INCLUDE_DIRS}
)

target_link_libraries(
  socket
    PRIVATE
      pthread
)
