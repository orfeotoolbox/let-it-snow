file(GLOB hdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.h")
file(GLOB thdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.txx")

# Build our library
add_library( histo_utils SHARED histo_utils.cxx )
target_link_libraries(histo_utils ${OTB_LIBRARIES})
# Define the wrapper library that wraps our library
add_library( histo_utils_ext SHARED histo_utils_ext.cxx )
target_link_libraries( histo_utils_ext ${Boost_LIBRARIES} ${PYTHON_LIBRARIES} histo_utils )
# don't prepend wrapper library name with lib
set_target_properties( histo_utils_ext PROPERTIES PREFIX "" )

# Build snow line exe
add_executable(compute_snowline compute_snowline.cxx)
target_link_libraries(compute_snowline histo_utils)

# Install for executables and libraries
install(TARGETS compute_snowline histo_utils histo_utils_ext
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib/static)

# Create the ComputeCloudMask OTB application
otb_create_application(NAME           ComputeCloudMask
                       SOURCES        ComputeCloudMask.cxx
                       LINK_LIBRARIES ${OTB_LIBRARIES})

# Create the ComputeSnowMask OTB application
otb_create_application(NAME           ComputeSnowMask
                       SOURCES        ComputeSnowMask.cxx
                       LINK_LIBRARIES ${OTB_LIBRARIES})
