cmake_minimum_required(VERSION 2.4)
if(COMMAND cmake_policy)
    cmake_policy(SET CMP0003 NEW)
    cmake_policy(SET CMP0012 NEW)
endif(COMMAND cmake_policy)

set(projName "standAlongForTest")
project(${projName})

add_definitions ("-Wall")

set(CMAKE_C_FLAGS "-Wall -fmax-errors=1 -Wfatal-errors")
set(CMAKE_CXX_FLAGS "-Wall -fmax-errors=1 -Wfatal-errors")

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED on)

#--------------------------------------------------------------------------------
# Set a default build type if none was specified
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  message(STATUS "Setting build type to 'Release' as none was specified.")
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
  # Set the possible values of build type for cmake-gui
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()


#--------------------------------------------------------------------------------
set(projectLibraryAll "")


#--------------------------------------------------------------------------------
# ITK
find_package (ITK REQUIRED)
include(${ITK_USE_FILE})
set(projectLibraryAll
  ${ITK_LIBRARIES}
  ${TIFF_LIBRARIES}
  ${projectLibraryAll}
  )


#--------------------------------------------------------------------------------
# VTK
find_package (VTK REQUIRED)
include(${VTK_USE_FILE})
set(projectLibraryAll
  ${VTK_LIBRARIES}
  ${projectLibraryAll}
  )


################################################################################
# include sub-dirs
set(exeFileName mainDijkstraGraphGeodesicPath)
option(build_${exeFileName} "build ${exeFileName}?" ON)
if (build_${exeFileName})
    set(cexx ${exeFileName})
    add_executable(${cexx} ${cexx}.cxx)
    target_link_libraries(${cexx} ${projectLibraryAll})
endif (build_${exeFileName})


set(exeFileName mainDijkstraGraphGeodesicPath1)
option(build_${exeFileName} "build ${exeFileName}?" ON)
if (build_${exeFileName})
    set(cexx ${exeFileName})
    add_executable(${cexx} ${cexx}.cxx)
    target_link_libraries(${cexx} ${projectLibraryAll})
endif (build_${exeFileName})
