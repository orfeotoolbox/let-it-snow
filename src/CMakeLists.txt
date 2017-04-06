file(GLOB hdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.h")
file(GLOB thdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.txx")

# Build our library
add_library( histo_utils SHARED histo_utils.cxx )
target_link_libraries(histo_utils ${OTB_LIBRARIES})
# Define the wrapper library that wraps our library
add_library( histo_utils_ext SHARED histo_utils_ext.cxx )
target_link_libraries( histo_utils_ext ${Boost_LIBRARIES} histo_utils )
# don't prepend wrapper library name with lib
set_target_properties( histo_utils_ext PROPERTIES PREFIX "" )

#Build SEB snow all mask exe
add_executable(compute_snow_mask compute_snow_mask.cxx)
target_link_libraries(compute_snow_mask ${OTB_LIBRARIES})

#Build cloud mask exe
add_executable(compute_cloud_mask compute_cloud_mask.cxx)
target_link_libraries(compute_cloud_mask ${OTB_LIBRARIES})

#Build snow line exe
add_executable(compute_snowline compute_snowline.cxx)
target_link_libraries(compute_snowline histo_utils)
