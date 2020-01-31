cmake_minimum_required(VERSION 2.8)
project(LISOTBModule)


# This module create a library, with the same name as the module
set(LISOTBModule_LIBRARIES LISOTBModule)

if(NOT OTB_SOURCE_DIR)
  # Handle the compilation outside OTB source tree: find where OTB is built/installed
  find_package(OTB REQUIRED)
  list(APPEND CMAKE_MODULE_PATH ${OTB_CMAKE_DIR})
  include(${OTB_USE_FILE})

  # The Python interpreter is needed for Python tests
  set(Python_ADDITIONAL_VERSIONS "3")
  find_package( PythonInterp REQUIRED)

  # This script will process the module sources
  include(OTBModuleExternal)
else()
  otb_module_impl()
endif()



# Execute and Copy during installation
install(DIRECTORY python_src DESTINATION  ${CMAKE_INSTALL_PREFIX})
install(DIRECTORY python_include DESTINATION  ${CMAKE_INSTALL_PREFIX})



#if(UNIX)
#install(CODE "execute_process(COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/scripts/generate_diapOTBEnv.sh ${CMAKE_INSTALL_PREFIX})")
#install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/scripts/diapOTBEnv.sh PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ DESTINATION #${CMAKE_INSTALL_PREFIX})
#endif()

