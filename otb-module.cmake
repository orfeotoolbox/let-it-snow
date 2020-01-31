set(DOCUMENTATION "OTB module for snow cover extent detection algorithm LIS.")

# otb_module() defines the module dependencies of ExternalTemplate.
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
# (ExternalTemplateExport.h), so that other binaries can link to this library.



# define the dependencies of the include module and the tests
otb_module(LISOTBModule
  ENABLE_SHARED
  DEPENDS
    OTBCommon
    OTBBoost
    OTBApplicationEngine
    OTBConvolution
    OTBMetadata
  TEST_DEPENDS
    OTBTestKernel
    OTBCommandLine
  DESCRIPTION
    "${DOCUMENTATION}"
)
