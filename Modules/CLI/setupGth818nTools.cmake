#--------------------------------------------------------------------------------
# OMP
find_package(OpenMP)
if(OPENMP_FOUND)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_EXE_LINKER_FLAGS}")
endif()


#--------------------------------------------------------------------------------
# find GTH818N path
set(GTH818N_PATH ${Slicer_SOURCE_DIR}/Libs/gth818n/)

include_directories(${GTH818N_PATH})

#--------------------------------------------------------------------------------
# my libs
add_library(GTH818N_LIBRARIES
  ${GTH818N_PATH}/fibheap.cpp
  )

