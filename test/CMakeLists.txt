ENABLE_TESTING()

INCLUDE(Dart)

mark_as_advanced(LIS_DATA_ROOT)

set(BASELINE ${LIS_DATA_ROOT}/Baseline)
set(DATA_TEST ${LIS_DATA_ROOT}/Input-Data-Test)
set(OUTPUT_TEST ${CMAKE_BINARY_DIR}/Testing/Temporary)

#TODO need to pass env variable propoerly using qgis code
#SET(ENV{PYTHONPATH} \"${CMAKE_BINARY_DIR}/bin/:\$ENV{PYTHONPATH}\")
#MESSAGE(\"PYTHONPATH:\$ENV{PYTHONPATH}\")


add_test(NAME test_json_builder_test 
	COMMAND ${CMAKE_SOURCE_DIR}/test/test_json_builder.sh
	"${CMAKE_SOURCE_DIR}/config"
	"${DATA_TEST}/Take5/AOI_test_CESNeige"
	"${OUTPUT_TEST}"
	)

add_test(NAME s2snow_test
  COMMAND ${PYTHON_EXECUTABLE}
  ${CMAKE_SOURCE_DIR}/app/s2snow.py ${CMAKE_SOURCE_DIR}/config/param_test.json
  )
set_tests_properties(s2snow_test PROPERTIES DEPENDS test_json_builder_test)
	
add_test(NAME compare_snow_output_pass1_test
  COMMAND ${CMAKE_COMMAND} -E compare_files
  "${OUTPUT_TEST}/pass1.tif" 
  "${BASELINE}/pass1.tif"
  )
set_tests_properties(compare_snow_output_pass1_test PROPERTIES DEPENDS s2snow_test)

add_test(NAME compare_snow_output_pass2_test
  COMMAND ${CMAKE_COMMAND} -E compare_files
  "${OUTPUT_TEST}/pass2.tif" 
  "${BASELINE}/pass2.tif"
  )
set_tests_properties(compare_snow_output_pass2_test PROPERTIES DEPENDS s2snow_test)

add_test(NAME compare_snow_output_pass3_test
  COMMAND ${CMAKE_COMMAND} -E compare_files
  "${OUTPUT_TEST}/pass3.tif" 
  "${BASELINE}/pass3.tif"
  )
set_tests_properties(compare_snow_output_pass1_test PROPERTIES DEPENDS s2snow_test)


add_test(NAME compare_snow_output_final_mask_test
  COMMAND ${CMAKE_COMMAND} -E compare_files
  "${OUTPUT_TEST}/final_mask.tif" 
  "${BASELINE}/final_mask.tif"
  )
set_tests_properties(compare_snow_output_final_mask_test PROPERTIES DEPENDS s2snow_test)

add_test(NAME preprocessing_test
  COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_SOURCE_DIR}/utils/preprocessing.py 
  "${DATA_TEST}/SRTM/sud_ouest.vrt"
  "${DATA_TEST}/Landsat/LANDSAT8_OLITIRS_XS_20150312_N2A_ORTHO_SURF_CORR_PENTE_France-MetropoleD0005H0001.TIF"
  "${OUTPUT_TEST}/landsat_bassies_srtm.tif"
  )

add_test(NAME compare_preprocessing_output_test
  COMMAND ${CMAKE_COMMAND} -E compare_files
  "${OUTPUT_TEST}/landsat_bassies_srtm.tif" 
  "${BASELINE}/landsat_bassies_srtm.tif"
  )

ADD_EXECUTABLE(histo_utils_test histo_utils_test.cxx)
TARGET_LINK_LIBRARIES(histo_utils_test histo_utils)

ADD_EXECUTABLE(histo_utils_ng_test histo_utils_ng_test.cxx)
TARGET_LINK_LIBRARIES(histo_utils_ng_test histo_utils)

ADD_EXECUTABLE(histo_utils_ng_internal_test histo_utils_ng_internal_test.cxx)
TARGET_LINK_LIBRARIES(histo_utils_ng_internal_test histo_utils)


ADD_EXECUTABLE(histo_utils_snow_fraction_test histo_utils_snow_fraction_test.cxx)
TARGET_LINK_LIBRARIES(histo_utils_snow_fraction_test histo_utils)

add_test(NAME histo_utils_ng_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_ng_test
    "${DATA_TEST}/Take5/AOI_test_CESNeige/SRTM/Maroc/Maroc.tif"
    "${BASELINE}/pass1.tif"
    "${BASELINE}/cloud_refine.tif"
    100
    0.1
    2721
    )

add_test(NAME histo_utils_ng_internal_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_ng_internal_test
    0
    100
    20
    0.1
    "${BASELINE}/histogram.txt"
    40
    )

add_test(NAME histo_utils_full_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_ng_test
    "${BASELINE}/srtm_superimpose.tif"
    "${BASELINE}/pass1_full.tif"
    "${BASELINE}/cloud_refine_full.tif"
    100
    0.1
    2920
    )

add_test(NAME histo_utils_ng_full_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_ng_test
    "${BASELINE}/srtm_superimpose.tif"
    "${BASELINE}/pass1_full.tif"
    "${BASELINE}/cloud_refine_full.tif"
    100
    0.1
    2920
    )

add_test(NAME histo_utils_snow_fraction_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_snow_fraction_test
    "${BASELINE}/pass1.tif"
    127784
    )