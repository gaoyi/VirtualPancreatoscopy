
#-----------------------------------------------------------------------------
set(MODULE_NAME CoronaryArteryAnalysis)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )



# ################################################################################
# ################################################################################
# ################################################################################
# cmake_minimum_required(VERSION 2.8.9)

# project(CoronaryArteryAnalysis)

# #-----------------------------------------------------------------------------
# # Extension meta-information
# set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/CoronaryArteryAnalysis")
# set(EXTENSION_CATEGORY "CoronaryArtery")
# set(EXTENSION_CONTRIBUTORS "Yi Gao")
# set(EXTENSION_DESCRIPTION "This is an extension for coronary artery analysis")
# set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/CoronaryArteryAnalysis.png")
# set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/CoronaryArteryAnalysis/Screenshots/1.png")
# set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

# #-----------------------------------------------------------------------------
# # Extension dependencies
# find_package(Slicer REQUIRED)
# include(${Slicer_USE_FILE})

# #--------------------------------------------------------------------------------
# # OMP
# find_package(OpenMP)
# if(OPENMP_FOUND)
#     set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
#     set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
#     set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_EXE_LINKER_FLAGS}")
# endif()

# #--------------------------------------------------------------------------------
# # find GTH818N path
# #--------------------------------------------------------------------------------
# find_path(GTH818N_PATH Technique/Image/gth818nImageIO.h HINTS $ENV{HOME}/usr/work/gth818n)
# if(NOT GTH818N_PATH)
#    message(FATAL_ERROR "Please enter the installation path of gth818n")
# endif(NOT GTH818N_PATH)

# include_directories(${GTH818N_PATH})
# add_library(GTH818N_LIBRARIES
#   ${GTH818N_PATH}/Technique/ThirdParty/fibheap/fibheap.cpp
#   )


# #-----------------------------------------------------------------------------
# # Extension modules
# # add_subdirectory(CoronaryArteryExtraction)
# add_subdirectory(CoronaryArteryAnalysis)
# add_subdirectory(ComputeVesselness)
# add_subdirectory(ComputeAxisFromVesselness)
# add_subdirectory(ComputeBranchAxis)
# add_subdirectory(SegmentLumenFromAxis)
# add_subdirectory(BuildMSTFromFudicuals)
# add_subdirectory(ComputeVesselFromSkeleton)
# #add_subdirectory(OptimalTracing)
# ## NEXT_MODULE

# #-----------------------------------------------------------------------------
# include(${Slicer_EXTENSION_CPACK})
