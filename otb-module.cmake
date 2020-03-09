set(DOCUMENTATION "LIS (Let It Snow) OTB Module.")

otb_module(LIS
  DEPENDS
    OTBCommon
    OTBApplicationEngine
    OTBStatistics
    OTBImageBase
    OTBImageIO
    OTBITK
  TEST_DEPENDS
    OTBTestKernel
    OTBCommandLine
    OTBSWIGWrapper
  DESCRIPTION
    "${DOCUMENTATION}"
)
