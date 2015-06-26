file(GLOB hdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.h")
file(GLOB thdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.txx")

# Build our library
add_library( compute_zs SHARED compute_zs.cxx )
target_link_libraries(compute_zs ${OTB_LIBRARIES})
# Define the wrapper library that wraps our library
add_library( compute_zs_ext SHARED compute_zs_ext.cxx )
target_link_libraries( compute_zs_ext ${Boost_LIBRARIES} compute_zs )
# don't prepend wrapper library name with lib
set_target_properties( compute_zs_ext PROPERTIES PREFIX "" )

# ADD_EXECUTABLE(test_histo main.cxx ${hdrs} ${thdrs})
# TARGET_LINK_LIBRARIES(test_histo ${OTB_LIBRARIES})

# ADD_EXECUTABLE(histo_lis main2.cxx ${hdrs} ${thdrs})
# TARGET_LINK_LIBRARIES(histo_lis ${OTB_LIBRARIES})
