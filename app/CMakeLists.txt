
# This macro creates the application EmptyApp. It must be linked to
# OTBApplicationEngine. Since the module has its own library,
# the variable ${otb-module}_LIBRARIES only contains this library, which doesn't
# drag OTBApplicationEngine, so we need to add it explicitely.


message(${${otb-module}_LIBRARIES})


# Create the ComputeCloudMask OTB application
OTB_CREATE_APPLICATION(NAME           ComputeCloudMask
                      SOURCES        otbComputeCloudMask.cxx
                      #LINK_LIBRARIES ${OTB_LIBRARIES})
                      LINK_LIBRARIES ${${otb-module}_LIBRARIES}
                      )

# Create the ComputeSnowMask OTB application
OTB_CREATE_APPLICATION(NAME           ComputeSnowMask
                       SOURCES        otbComputeSnowMask.cxx
                       LINK_LIBRARIES ${${otb-module}_LIBRARIES}
                       )
 
# Create the ComputeContour OTB application
OTB_CREATE_APPLICATION(NAME           ComputeContours
                       SOURCES        otbComputeContours.cxx
                       LINK_LIBRARIES ${${otb-module}_LIBRARIES}
                       )

# Create the ComputeSnowLine OTB application
#OTB_CREATE_APPLICATION(NAME           ComputeSnowLine
#                       SOURCES        otbComputeSnowLine.cxx
#                       LINK_LIBRARIES ${${otb-module}_LIBRARIES})

# Create the ComputeNbPixels OTB application
OTB_CREATE_APPLICATION(NAME           ComputeNbPixels
                       SOURCES        otbComputeNbPixels.cxx
                       LINK_LIBRARIES ${${otb-module}_LIBRARIES}
                       )                   

