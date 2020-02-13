cmake_minimum_required(VERSION 3.10.2)
project(LIS)

if(NOT OTB_SOURCE_DIR)
  # Handle the compilation outside OTB source tree: find where OTB is built/installed
  find_package(OTB REQUIRED)
  list(APPEND CMAKE_MODULE_PATH ${OTB_CMAKE_DIR})
  include(UseOTB)

  # The Python interpreter is needed for Python tests
  set(Python_ADDITIONAL_VERSIONS "3")
  find_package( PythonInterp REQUIRED)

  # This script will process the module sources
  include(OTBModuleExternal)
else()
  otb_module_impl()
endif()
