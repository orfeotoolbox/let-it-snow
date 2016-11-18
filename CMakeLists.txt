PROJECT(lis)

CMAKE_MINIMUM_REQUIRED(VERSION 2.8)

include_directories(src)

# Find necessary packages

find_package(GDAL REQUIRED)


if(NOT GDAL_FOUND)
 message(FATAL_ERROR "Cannot find GDAL. Set GDAL_INCLUDE_DIR and GDAL_LIBRARY")
endif()

if (GDAL_CONFIG) 
  ## extract gdal version 
  exec_program(${GDAL_CONFIG}
    ARGS --version
    OUTPUT_VARIABLE GDAL_VERSION )
  string(REGEX REPLACE "([0-9]+)\\.([0-9]+)\\.([0-9]+)" "\\1" GDAL_VERSION_MAJOR "${GDAL_VERSION}")
  string(REGEX REPLACE "([0-9]+)\\.([0-9]+)\\.([0-9]+)" "\\2" GDAL_VERSION_MINOR "${GDAL_VERSION}")
  
  #MESSAGE("DBG GDAL_VERSION ${GDAL_VERSION}")
  #MESSAGE("DBG GDAL_VERSION_MAJOR ${GDAL_VERSION_MAJOR}")
  #MESSAGE("DBG GDAL_VERSION_MINOR ${GDAL_VERSION_MINOR}")
  
  # check for gdal version
  if (GDAL_VERSION_MAJOR LESS 2)
    message (FATAL_ERROR "GDAL version is too old (${GDAL_VERSION}). Use 2.1 or higher.")
  endif ()
endif()

#Set python home (needed on the cnes cluster)
set(PYTHON_INCLUDE_DIRS $ENV{PYTHONHOME}/include)

find_package(PythonInterp REQUIRED)

find_package( PythonLibs 2.7 REQUIRED)
include_directories( ${PYTHON_INCLUDE_DIRS} )
 
find_package( Boost COMPONENTS python REQUIRED )

include_directories( ${Boost_INCLUDE_DIR} )

# Link to the Orfeo ToolBox
FIND_PACKAGE(OTB)
IF(OTB_FOUND)
  INCLUDE(${OTB_USE_FILE})
ELSE(OTB_FOUND)
  MESSAGE(FATAL_ERROR
          "OTB not found. Please set OTB_DIR")
ENDIF(OTB_FOUND)


# Output directories
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${lis_BINARY_DIR}/bin CACHE INTERNAL "Single output directory for all ARCHIVE products (static libs, import libs)")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${lis_BINARY_DIR}/bin CACHE INTERNAL "Single output directory for all LIBRARY products (so, modules)")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${lis_BINARY_DIR}/bin CACHE INTERNAL "Single output directory for all RUNTIME products (executables, dlls)")

# Install dirs
if(NOT lis_INSTALL_BIN_DIR)
  set(lis_INSTALL_BIN_DIR "bin")
endif(NOT lis_INSTALL_BIN_DIR)

if(NOT lis_INSTALL_LIB_DIR)
  set(lis_INSTALL_LIB_DIR "lib")
endif(NOT lis_INSTALL_LIB_DIR)

if(NOT lis_INSTALL_INCLUDE_DIR)
  set(lis_INSTALL_INCLUDE_DIR "include")
endif(NOT lis_INSTALL_INCLUDE_DIR)

SET(BUILD_SHARED_LIBS ON)

add_subdirectory(src)
add_subdirectory(python)
add_subdirectory(app)
# Add Testing subdirectory
option(BUILD_TESTING  "Build testing." OFF)

if(BUILD_TESTING)
    ENABLE_TESTING()
    INCLUDE(Dart)
    add_subdirectory(test)
endif()
