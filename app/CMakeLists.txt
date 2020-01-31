
# Build our library
add_library( histo_utils SHARED histo_utils.cxx )
target_link_libraries(histo_utils ${OTB_LIBRARIES})

# Install for executables and libraries
install(TARGETS histo_utils
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib/static)

# Create the ComputeCloudMask OTB application
otb_create_application(NAME           ComputeCloudMask
                       SOURCES        otbComputeCloudMask.cxx
                       LINK_LIBRARIES ${OTB_LIBRARIES})

# Create the ComputeSnowMask OTB application
otb_create_application(NAME           ComputeSnowMask
                       SOURCES        otbComputeSnowMask.cxx
                       LINK_LIBRARIES ${OTB_LIBRARIES})

# Create the ComputeContour OTB application
otb_create_application(NAME           ComputeContours
                       SOURCES        otbComputeContours.cxx
                       LINK_LIBRARIES ${OTB_LIBRARIES})

# Create the ComputeSnowLine OTB application
otb_create_application(NAME           ComputeSnowLine
                       SOURCES        otbComputeSnowLine.cxx
                       LINK_LIBRARIES ${OTB_LIBRARIES} histo_utils)

# Create the ComputeNbPixels OTB application
otb_create_application(NAME           ComputeNbPixels
                       SOURCES        otbComputeNbPixels.cxx
                       LINK_LIBRARIES ${OTB_LIBRARIES})
