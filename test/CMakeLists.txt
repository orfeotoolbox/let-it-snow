ENABLE_TESTING()

INCLUDE(Dart)

#TODO need to pass env variable propoerly using qgis code
#SET(ENV{PYTHONPATH} \"${CMAKE_BINARY_DIR}/bin/:\$ENV{PYTHONPATH}\")
#MESSAGE(\"PYTHONPATH:\$ENV{PYTHONPATH}\")

add_test(NAME s2snowTest
  COMMAND ${PYTHON_EXECUTABLE}
    ${CMAKE_SOURCE_DIR}/app/s2snow.py ${CMAKE_SOURCE_DIR}/app/param_extract_maroc.json
    )

ADD_EXECUTABLE(histo_utils_test histo_utils_test.cxx)
TARGET_LINK_LIBRARIES(histo_utils_test histo_utils)

add_test(NAME histo_utils_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_test
    "/home/grizonnetm/data/CES-Neige/test_CES/Take5/AOI_test_CESNeige/SRTM/Maroc/Maroc.tif"
    "/home/grizonnetm/data/CES-Neige/Baseline/pass1.tif"
    "/home/grizonnetm/data/CES-Neige/Baseline/cloud_refine.tif"
    100
    0.1
    )
