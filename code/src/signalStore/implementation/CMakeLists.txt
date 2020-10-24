cmake_minimum_required(VERSION 3.11.0 FATAL_ERROR)

add_library(
  inMemorySignalStore OBJECT
    inMemorySignalStore.h
    inMemorySignalStore.cpp
)

target_compile_options(
  inMemorySignalStore
    PRIVATE
      ${_s_compiler_warning_flags} -Wno-write-strings -Wno-memaccess 
)

target_include_directories(
  inMemorySignalStore
    PUBLIC
      $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
)

target_include_directories(
  inMemorySignalStore
    PUBLIC
      ${CMAKE_CURRENT_SOURCE_DIR}../domain/
      $<TARGET_PROPERTY:storeDomain,INTERFACE_INCLUDE_DIRECTORIES>
      ${RAPIDJSON_INCLUDE_DIRS}
)
#target_link_libraries(
#  inMemorySignalStore
#    PRIVATE 
#
#)
