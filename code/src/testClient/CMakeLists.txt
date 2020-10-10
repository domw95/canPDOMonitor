cmake_minimum_required(VERSION 3.11.0 FATAL_ERROR)

add_library(
  client OBJECT
    client.h
    client.cpp
)

target_compile_options(
  client
    PRIVATE
      ${_subco_compiler_warning_flags} -Wno-write-strings -Wno-memaccess
)

target_include_directories(
  client
    PUBLIC
      $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
)

