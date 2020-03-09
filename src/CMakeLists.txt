set(${otb-module}_DEPENDS)
if(NOT PROJECT_NAME STREQUAL "LIS")
  set(${otb-module}_DEPENDS OTBSWIGWrapper-all)
endif()

add_custom_target(${otb-module}-py
  COMMAND ${PYTHON_EXECUTABLE} setup.py build --build-base ${CMAKE_CURRENT_BINARY_DIR}/python
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/python
  DEPENDS ${${otb-module}_DEPENDS}
  )

otb_module_target_label(${otb-module}-py)

install(CODE "
message(STATUS \"Installing s2snow python package\")
execute_process(COMMAND ${PYTHON_EXECUTABLE} setup.py install
      --single-version-externally-managed \
      --record ${CMAKE_CURRENT_BINARY_DIR}/python/setup_install.log
      --home=${CMAKE_INSTALL_PREFIX} --install-purelib=${CMAKE_INSTALL_PREFIX}/${OTB_INSTALL_PYTHON_DIR} --install-scripts=bin
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/python
  RESULT_VARIABLE _install_rv
  OUTPUT_VARIABLE _install_ov
  ERROR_VARIABLE _install_ev)
  if(NOT \${_install_rv} EQUAL 0)
    message(FATAL_ERROR \"Failed to install s2snow(LIS) because \${_install_ov} \\n \${_install_ev}  \")
  endif()
")
