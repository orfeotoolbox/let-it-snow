OTB_CREATE_APPLICATION(NAME           ComputeCloudMask
                      SOURCES        otbComputeCloudMask.cxx
                      LINK_LIBRARIES ${${otb-module}_LIBRARIES}
                      )

OTB_CREATE_APPLICATION(NAME           ComputeSnowMask
                       SOURCES        otbComputeSnowMask.cxx
                       LINK_LIBRARIES ${${otb-module}_LIBRARIES}
                       )

OTB_CREATE_APPLICATION(NAME           ComputeContours
                       SOURCES        otbComputeContours.cxx
                       LINK_LIBRARIES ${${otb-module}_LIBRARIES}
                       )

OTB_CREATE_APPLICATION(NAME           ComputeSnowLine
                       SOURCES        otbComputeSnowLine.cxx ../src/histo_utils.cxx
                       LINK_LIBRARIES ${${otb-module}_LIBRARIES}
                       )

OTB_CREATE_APPLICATION(NAME           ComputeNbPixels
                       SOURCES        otbComputeNbPixels.cxx
                       LINK_LIBRARIES ${${otb-module}_LIBRARIES}
                       )
