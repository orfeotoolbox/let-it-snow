mark_as_advanced(LIS_DATA_ROOT)

set(BASELINE ${LIS_DATA_ROOT}/Baseline)
set(DATA_TEST ${LIS_DATA_ROOT}/Input-Data-Test)
set(OUTPUT_TEST ${CMAKE_BINARY_DIR}/Testing/Temporary)

#TODO need to pass env variable propoerly using qgis code
#SET(ENV{PYTHONPATH} \"${CMAKE_BINARY_DIR}/bin/:\$ENV{PYTHONPATH}\")
#MESSAGE(\"PYTHONPATH:\$ENV{PYTHONPATH}\")

add_test(NAME test_json_builder_test 
	COMMAND ${CMAKE_SOURCE_DIR}/test/test_json_builder.sh
	"${CMAKE_CURRENT_SOURCE_DIR}"
	"${DATA_TEST}/Take5/AOI_test_CESNeige"
	"${OUTPUT_TEST}"
	)

add_test(NAME s2snow_test
  COMMAND ${PYTHON_EXECUTABLE}
  ${CMAKE_SOURCE_DIR}/app/run_snow_detector.py ${OUTPUT_TEST}/param_test.json
  )
set_tests_properties(s2snow_test PROPERTIES DEPENDS test_json_builder_test)
	
add_test(NAME compare_snow_output_pass1_test
  COMMAND gdalcompare.py
  "${BASELINE}/pass1_highcloud.tif"
  "${OUTPUT_TEST}/pass1.tif" 
  )
set_tests_properties(compare_snow_output_pass1_test PROPERTIES DEPENDS s2snow_test)

add_test(NAME compare_snow_output_pass2_test
  COMMAND gdalcompare.py
  "${BASELINE}/pass2_highcloud.tif"
  "${OUTPUT_TEST}/pass2.tif" 
  )
set_tests_properties(compare_snow_output_pass2_test PROPERTIES DEPENDS s2snow_test)

add_test(NAME compare_snow_output_pass3_test
  COMMAND gdalcompare.py
  "${BASELINE}/pass3_highcloud.tif"
  "${OUTPUT_TEST}/pass3.tif" 
  )
set_tests_properties(compare_snow_output_pass1_test PROPERTIES DEPENDS s2snow_test)

add_test(NAME preprocessing_test
  COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_SOURCE_DIR}/python/s2snow/dem_builder.py 
  "${DATA_TEST}/SRTM/sud_ouest.vrt"
  "${DATA_TEST}/Landsat/LANDSAT8_OLITIRS_XS_20150312_N2A_ORTHO_SURF_CORR_PENTE_France-MetropoleD0005H0001.TIF"
  "${OUTPUT_TEST}/landsat_bassies_srtm.tif"
  )

# add_test(NAME compare_preprocessing_output_test
#   COMMAND ${CMAKE_COMMAND} -E compare_files
#   "${OUTPUT_TEST}/landsat_bassies_srtm.tif" 
#   "${BASELINE}/landsat_bassies_srtm.tif"
#   )
# set_tests_properties(compare_preprocessing_output_test PROPERTIES DEPENDS s2snow_test)

add_test(NAME compare_final_mask_output_test
  COMMAND gdalcompare.py
  "${BASELINE}/final_mask_highcloud.tif"
  "${OUTPUT_TEST}/final_mask.tif" 
  )
set_tests_properties(compare_final_mask_output_test PROPERTIES DEPENDS s2snow_test)

#gdalcompare.py doesn't work on dbf files
add_test(NAME compare_final_mask_vec_output_test
  COMMAND ${CMAKE_COMMAND} -E compare_files
  "${BASELINE}/final_mask_vec_highcloud.dbf"
  "${OUTPUT_TEST}/final_mask_vec.dbf" 
  )
set_tests_properties(compare_final_mask_vec_output_test PROPERTIES DEPENDS s2snow_test)

add_test(NAME compare_snow_all_output_test
  COMMAND gdalcompare.py
  "${BASELINE}/snow_all_highcloud.tif"
  "${OUTPUT_TEST}/snow_all.tif" 
  )
set_tests_properties(compare_snow_all_output_test PROPERTIES DEPENDS s2snow_test)

ADD_EXECUTABLE(histo_utils_snowline_test histo_utils_snowline_test.cxx)
TARGET_LINK_LIBRARIES(histo_utils_snowline_test histo_utils)

ADD_EXECUTABLE(histo_utils_snowline_internal_test histo_utils_snowline_internal_test.cxx)
TARGET_LINK_LIBRARIES(histo_utils_snowline_internal_test histo_utils)

ADD_EXECUTABLE(histo_utils_snow_fraction_test histo_utils_snow_fraction_test.cxx)
TARGET_LINK_LIBRARIES(histo_utils_snow_fraction_test histo_utils)

add_test(NAME histo_utils_snowline_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_snowline_test
    "${DATA_TEST}/Take5/AOI_test_CESNeige/SRTM/Maroc/Maroc.tif"
    "${BASELINE}/pass1_highcloud.tif"
    "${BASELINE}/cloud_refine_highcloud.tif"
    100
    0.1
    0
    -2
    -50
    2721
    )

add_test(NAME histo_utils_snowline_internal_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_snowline_internal_test
    0
    100
    20
    0.1
    0
    -2
    -10
    "${BASELINE}/histogram_highcloud.txt"
    40
    )
add_test(NAME histo_utils_snowline_reverse_internal_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_snowline_internal_test
    0
    100
    20
    0.99
    1
    0
    0
    "${BASELINE}/histogram_reverse_highcloud.txt"
    90
    )


add_test(NAME histo_utils_snowline_full_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_snowline_test
    "${BASELINE}/srtm_superimpose_highcloud.tif"
    "${BASELINE}/pass1_full_highcloud.tif"
    "${BASELINE}/cloud_refine_full_highcloud.tif"
    100
    0.1
    0
    -2
    -50
    2920
    )

add_test(NAME histo_utils_snow_fraction_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/histo_utils_snow_fraction_test
    "${OUTPUT_TEST}/histo_utils_snow_fraction_test.tif"
    11
    )

add_test(NAME compute_snow_mask_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/compute_snow_mask
    "${BASELINE}/pass1_highcloud.tif"
    "${BASELINE}/pass2_highcloud.tif"
    "${BASELINE}/cloud_pass1_highcloud.tif"
    "${BASELINE}/cloud_refine_highcloud.tif"
    "${OUTPUT_TEST}/snow_all_test.tif"
     )

add_test(NAME compute_cloud_mask_test
  COMMAND ${CMAKE_BINARY_DIR}/bin/compute_cloud_mask
    "${DATA_TEST}/Take5/AOI_test_CESNeige/LEVEL2A/Maroc/SPOT4_HRVIR_XS_20130327_N2A_CMarocD0000B0000_NUA.TIF"
    "1"
    "${OUTPUT_TEST}/cloud_mask_test.tif"
     )

add_test(NAME cloud_removal_step3_test
  COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/cloud_removal_step3_test.py) 

add_test(NAME cloud_removal_step4_test
  COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/cloud_removal_step4_test.py)
