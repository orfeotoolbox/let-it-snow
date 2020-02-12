set(DOCUMENTATION "LIS (Let It Snow) OTB Module.")

# otb_module() defines the module dependencies of LISOTBModule.
# LISOTBModule depends on:
#   - OTBCommon (base dependency of all modules)
#   - OTBApplicationEngine (because we build an application in the module, see 'app' folder)
# 
# The tests of module LISOTBModule drag additional dependencies:
#   - OTBTestKernel (needed for any test driver)
#   - OTBCommandLine (needed to run tests on applications)
#   - OTBSWIG (needed to run tests with Python bindings)
#
# The option ENABLE_SHARED is needed because this module creates a shared
# library. It generates a header with usefull export macros
# (LISOTBModuleExport.h), so that other binaries can link to this library.

otb_module(LISOTBModule
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