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
