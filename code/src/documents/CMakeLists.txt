cmake_minimum_required(VERSION 3.11.0 FATAL_ERROR)

add_library(
  jsonRecord OBJECT
    jsonRecord.h
)

target_compile_options(
  jsonRecord
    PRIVATE
      ${_s_compiler_warning_flags} -Wno-write-strings
)

target_include_directories(
  jsonRecord
    PUBLIC
      $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
       ${RAPIDJSON_INCLUDE_DIRS}
)

