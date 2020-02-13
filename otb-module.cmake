set(DOCUMENTATION "LIS (Let It Snow) OTB Module.")

otb_module(LIS
  ENABLE_SHARED
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
    OTBSWIG
  DESCRIPTION
    "${DOCUMENTATION}"
)
