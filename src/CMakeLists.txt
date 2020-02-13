add_custom_target(${otb-module}-py
  COMMAND ${CMAKE_COMMAND} -E echo "Building python scrips ${CMAKE_CURRENT_BINARY_DIR}/python/"
  COMMAND ${PYTHON_EXECUTABLE} setup.py build --build-base ${CMAKE_CURRENT_BINARY_DIR}/python
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/python
  )
otb_module_target_label(${otb-module}-py)
