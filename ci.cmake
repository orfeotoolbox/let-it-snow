
# This script is a prototype for the future CI, it may evolve rapidly in a near future
set(REMOTE_MODULE_SOURCE_DIR ${CMAKE_CURRENT_LIST_DIR})
set (ENV{LANG} "C") # Only ascii output

# Get project name
file(STRINGS "${CMAKE_CURRENT_LIST_DIR}/CMakeLists.txt" _project_match REGEX "^project *\\(")
string(REGEX REPLACE "^project *\\( *([a-zA-Z0-9]+) *\\)" "\\1" otb-module ${_project_match})

# Build Configuration : Release, Debug..
if(ci_build_type)
  set (CTEST_BUILD_CONFIGURATION ${ci_build_type})
else()
  set (CTEST_BUILD_CONFIGURATION "Release")
endif()

set (CTEST_CMAKE_GENERATOR "Ninja")

# detect short sha
if(NOT DEFINED ENV{TRAVIS_COMMIT})
  execute_process(COMMAND git log -1 --pretty=format:%h
                  WORKING_DIRECTORY ${REMOTE_MODULE_SOURCE_DIR}
                  OUTPUT_VARIABLE ci_short_sha)
else()
  set(ci_short_sha "$ENV{TRAVIS_COMMIT}")
endif()

set(CTEST_PROJECT_NAME "${otb-module}")
set(CTEST_DROP_METHOD "https")
set(CTEST_DROP_SITE "cdash.orfeo-toolbox.org")
set(CTEST_DROP_LOCATION "/submit.php?project=OTB")
set(CTEST_DROP_SITE_CDASH TRUE)

set(CTEST_BUILD_NAME "${CTEST_PROJECT_NAME} ($ENV{TRAVIS_BRANCH})")
set(CTEST_SITE "$ENV{TRAVIS_OS_NAME}")
set(compiler_name "$ENV{TRAVIS_COMPILER}")
if("${CTEST_SITE}" STREQUAL "linux")
  set(CTEST_SITE "${CTEST_SITE}-$ENV{TRAVIS_DIST}")
elseif("${CTEST_SITE}" STREQUAL "osx")
  set(CTEST_SITE "${CTEST_SITE}-$ENV{TRAVIS_OSX_IMAGE}")
elseif("${CTEST_SITE}" STREQUAL "windows")
  set(CTEST_SITE "${CTEST_SITE}-server1803")
  set(compiler_name "vc140")
endif()
set(CTEST_SITE "${CTEST_SITE}-${compiler_name}")

# Detect "skip testing"
if(DEFINED ENV{CI_SKIP_TESTING})
  set(ci_skip_testing 1)
endif()

# Directory variable
set (CTEST_SOURCE_DIRECTORY "${REMOTE_MODULE_SOURCE_DIR}")
if(BUILD_DIR)
  set (CTEST_BINARY_DIRECTORY "${BUILD_DIR}")
else()
  set (CTEST_BINARY_DIRECTORY "${REMOTE_MODULE_SOURCE_DIR}/build/")
endif()
if(INSTALL_DIR)
  set (CTEST_INSTALL_DIRECTORY "${INSTALL_DIR}")
else()
  set (CTEST_INSTALL_DIRECTORY "${REMOTE_MODULE_SOURCE_DIR}/install/")
endif()
set (PROJECT_SOURCE_DIR "${REMOTE_MODULE_SOURCE_DIR}")

# Ctest command value
set (CMAKE_COMMAND "cmake")

# Set the CONFIGURE_OPTIONS variable
set (all_options
"BUILD_SHARED_LIBS:BOOL=ON
BUILD_TESTING:BOOL=ON
OTB_BUILD_MODULE_AS_STANDALONE:BOOL=ON
CMAKE_PREFIX_PATH:PATH=${REMOTE_MODULE_SOURCE_DIR}/xdk
CMAKE_INSTALL_PREFIX:PATH=${CTEST_INSTALL_DIRECTORY}
CMAKE_BUILD_TYPE=${CTEST_BUILD_CONFIGURATION}")

if(UNIX AND NOT APPLE)
set(all_options
"${all_options}
OpenGL_GL_PREFERENCE=GLVND")
endif()

if(APPLE)
set(all_options
"${all_options}
CMAKE_MACOSX_RPATH=TRUE")
endif()

string (REPLACE "\n" ";" rm_options ${all_options})
foreach(item ${rm_options})
  set( CONFIGURE_OPTIONS "${CONFIGURE_OPTIONS}-D${item};")
endforeach(item)

# Sources are already checked out : do nothing for update
set(CTEST_GIT_UPDATE_CUSTOM "${CMAKE_COMMAND}" "-E" "echo" "No update")

# Look for a GIT command-line client.
find_program(CTEST_GIT_COMMAND NAMES git git.cmd)

# Add bin dir to PATH for testing on Windows
if(WIN32)
  file(TO_NATIVE_PATH "${CTEST_BINARY_DIRECTORY}/bin" RM_BUILD_BIN_DIR_NATIVE)
  set(ENV{PATH} "$ENV{PATH};${RM_BUILD_BIN_DIR_NATIVE}" )
endif()

# Get Data from OTB :
#   - Use this flag to get the full data
set(RM_GET_FULL_DATA OFF)
#   - Or give a list of patterns
set(RM_DATA_PATTERNS)

set(RM_DATA_REF develop)
if (RM_GET_FULL_DATA OR RM_DATA_PATTERNS)
  message(STATUS "Retrieve data files from OTB")
  execute_process(COMMAND git clone -b ${RM_DATA_REF} --depth 1 -n https://gitlab.orfeo-toolbox.org/orfeotoolbox/otb.git
                  WORKING_DIRECTORY ${REMOTE_MODULE_SOURCE_DIR})
  if(RM_GET_FULL_DATA)
    message(STATUS "  Get full data")
  else()
    string(REPLACE ";" "," lfs_includes "${RM_DATA_PATTERNS}")
    message(STATUS "  Get paths: ${RM_DATA_PATTERNS}")
    execute_process(COMMAND git config lfs.fetchinclude "${lfs_includes}"
                    WORKING_DIRECTORY ${REMOTE_MODULE_SOURCE_DIR}/otb)
  endif()
  execute_process(COMMAND git lfs fetch
                  WORKING_DIRECTORY ${REMOTE_MODULE_SOURCE_DIR}/otb)
  execute_process(COMMAND git reset HEAD *
                  WORKING_DIRECTORY ${REMOTE_MODULE_SOURCE_DIR}/otb
                  OUTPUT_QUIET)
  execute_process(COMMAND git checkout -- Data/*
                  WORKING_DIRECTORY ${REMOTE_MODULE_SOURCE_DIR}/otb)
  set( CONFIGURE_OPTIONS "${CONFIGURE_OPTIONS}-DOTB_DATA_ROOT:PATH=${REMOTE_MODULE_SOURCE_DIR}/otb/Data;")
endif()

# End of configuration

ctest_start (Experimental TRACK RemoteModules)

ctest_update()

# --------------------------- Configure ----------------------------------------
ctest_configure(BUILD "${CTEST_BINARY_DIRECTORY}"
    SOURCE "${REMOTE_MODULE_SOURCE_DIR}"
    OPTIONS "${CONFIGURE_OPTIONS}"
    RETURN_VALUE _configure_rv
    CAPTURE_CMAKE_ERROR _configure_error
    )
# Configure log
file ( WRITE 
  "${REMOTE_MODULE_SOURCE_DIR}/log/configure_return_value_log.txt" "${_configure_rv}")
file ( WRITE 
  "${REMOTE_MODULE_SOURCE_DIR}/log/configure_cmake_error_log.txt" "${_configure_error}")

if ( NOT _configure_rv EQUAL 0 )
  # stop processing here
  ctest_submit()
  message( FATAL_ERROR "An error occurs during ctest_configure.")
endif()

# ------------------------------ Build -----------------------------------------
if(ci_skip_install)
  message(STATUS "Skip install")
  if (ci_build_target)
    message(STATUS "Building target: ${ci_build_target}")
    set(CTEST_BUILD_TARGET ${ci_build_target})
  else()
    set(CTEST_BUILD_TARGET)
  endif()
else()
  set(CTEST_BUILD_TARGET install)
endif()

ctest_build(BUILD "${CTEST_BINARY_DIRECTORY}"
            RETURN_VALUE _build_rv
            CAPTURE_CMAKE_ERROR _build_error
            )
# Build log
file ( WRITE 
  "${REMOTE_MODULE_SOURCE_DIR}/log/build_return_value_log.txt" "${_build_rv}")
file ( WRITE 
  "${REMOTE_MODULE_SOURCE_DIR}/log/build_cmake_error_log.txt" "${_build_error}")

if ( NOT _build_rv EQUAL 0 )
  message( SEND_ERROR "An error occurs during ctest_build.")
endif()

# ----------------------------- Test -------------------------------------------
if(ci_skip_testing)
  message(STATUS "Skip testing")
  set(_test_rv 0)
else()
  ctest_test(PARALLEL_LEVEL 2
             RETURN_VALUE _test_rv
             CAPTURE_CMAKE_ERROR _test_error
             )
  # Test log
  file ( WRITE 
    "${REMOTE_MODULE_SOURCE_DIR}/log/test_return_value_log.txt" "${_test_rv}")
  file ( WRITE 
    "${REMOTE_MODULE_SOURCE_DIR}/log/test_cmake_error_log.txt" "${_test_error}")
endif()

if ( NOT _test_rv EQUAL 0 )
  message( SEND_ERROR "An error occurs during ctest_test.")
endif()

# ----------------------------- Submit -----------------------------------------
if(ci_skip_submit)
  message(STATUS "Skip submit")
else()
  ctest_submit()
endif()
