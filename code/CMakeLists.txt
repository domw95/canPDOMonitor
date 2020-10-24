cmake_minimum_required(VERSION 3.11.0 FATAL_ERROR)

#
# TODO(jjad): !! This needs tidying, but holding off until basic PoC functional. !!
#
include(/opt/pegasus/cmake/Modules/Pegasus.cmake)
pegasus_minimum_required(VERSION 1.3.0-0)
set_pegasus_build_env()


# This if statement provides the opportunity to override the project's version on the command line
if ("${CAN_PDO_MONITOR_VERSION}" STREQUAL "")
  # If no version is provided, we assume it's a dev build which are all versioned 0.0.0
  set(CAN_PDO_MONITOR_VERSION 0.0.0)
endif()

project(can_pod_monitor VERSION ${CAN_PDO_MONITOR_VERSION})
include("${CMAKE_SOURCE_DIR}/vendor/rapidjson.cmake")
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${RAPIDJSON_INCLUDE_DIR}
)

list(INSERT CMAKE_MODULE_PATH 0 ${CMAKE_CURRENT_SOURCE_DIR}/cmake)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if (CMAKE_COMPILER_IS_GNUCC)
  set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0")
  set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -O0")
  set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3")
  set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -O3")
endif()
# known bug in pegasus-cmake-modules find_hydra_lib(Boost INSTALL_RPATH) doesn't work
set(CMAKE_INSTALL_RPATH
  "${CMAKE_INSTALL_RPATH}:/opt/hydra/x86_64/boost-1.63.0/lib")

set (CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
# One way to get $ORIGIN on the RPATH (other methods kept expanding $ORIGIN to RIGIN)
set(CMAKE_EXE_LINKER_FLAGS
  "${CMAKE_EXE_LINKER_FLAGS} -Wl,-rpath,'$ORIGIN/../lib'")

# Obey visibility flags of static libraries
set(CMAKE_SHARED_LINKER_FLAGS
  "${CMAKE_SHARED_LINKER_FLAGS} -Wl,-rpath,'$ORIGIN/../lib',--exclude-libs,ALL")

# TODO(mav) - set(CT_PUBLIC_API_FLAGS -fvisibility=hidden -fvisibility-inlines-hidden -Wno-attributes)

#
# Find dependencies
#

# jjad fucking hates linting
#find_hydra_lib(cpplint VERSION 0.0.7 ARCHITECTURE noarch)
find_hydra_lib(log4cxx VERSION 0.10.0 INSTALL_RPATH)
find_hydra_lib(libpcap VERSION 1.9.0 INSTALL_RPATH)

pegasus_cppcheck(
  EXCLUDE_PATTERNS ${S_STATIC_ANALYSIS_EXCLUDES}
  ARGS
    "--platform=unix64"
    "--std=c++14"
    "--language=c++"
    "--xml"
    "--xml-version=2"
    "--enable=all"
    "--suppress=syntaxError"
    "--suppress=missingInclude"
    "--suppress=unusedFunction"
    "--suppress=unusedPrivateFunction"
    "--inline-suppr"
)
#jjad really fucking hates pegasus linting
#pegasus_cpplint(
#  EXCLUDE_PATTERNS ${S_STATIC_ANALYSIS_EXCLUDES}
#)

#
# Continue to configure the project for compilation
#
add_subdirectory(src)
add_subdirectory(vendor)
