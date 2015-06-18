file(GLOB hdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.h")
file(GLOB thdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.txx")

ADD_EXECUTABLE(test_histo main.cxx ${hdrs} ${thdrs})
TARGET_LINK_LIBRARIES(test_histo ${OTB_LIBRARIES})

ADD_EXECUTABLE(histo_lis main2.cxx ${hdrs} ${thdrs})
TARGET_LINK_LIBRARIES(histo_lis ${OTB_LIBRARIES})
