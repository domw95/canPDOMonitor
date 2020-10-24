cmake_minimum_required(VERSION 3.11.0 FATAL_ERROR)

add_executable(
  testApp
     $<TARGET_OBJECTS:socket>
     $<TARGET_OBJECTS:client>
    coreWorkflow.h 
    coreWorkflow.cpp 
  main.cpp
)

target_include_directories(
  testApp
    PRIVATE
      $<TARGET_PROPERTY:socket,INTERFACE_INCLUDE_DIRECTORIES>
      $<TARGET_PROPERTY:client,INTERFACE_INCLUDE_DIRECTORIES>
)
target_link_libraries(
  testApp
    PRIVATE
      pthread
)

target_compile_options(
  testApp
    PRIVATE
       ${_s_compiler_warning_flags} -Wno-write-strings -Wno-memaccess
)

install(
  TARGETS testApp
)
