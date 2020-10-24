cmake_minimum_required(VERSION 3.11.0 FATAL_ERROR)

add_library(
  storeDomain OBJECT
    Store.h
)

target_compile_options(
  storeDomain
    PRIVATE
      ${_s_compiler_warning_flags} -Wno-write-strings -Wno-class-memaccess
)
target_include_directories(
  storeDomain
    PUBLIC
      $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
)

target_include_directories(
  storeDomain
    PRIVATE
      $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
      ${RAPIDJSON_INCLUDE_DIRS}
)
