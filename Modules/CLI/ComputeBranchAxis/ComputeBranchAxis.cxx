#include <algorithm>

#include <omp.h>

#include "SeededOptimalPathFilter3D.h"

#include "itkImageFileWriter.h"

#include "itkPluginUtilities.h"

#include "ComputeBranchAxisCLP.h"

// Use an anonymous namespace to keep class types and function names
// from colliding when module is used as shared object module.  Every
// thing should be in an anonymous namespace except for the module
// entry point, e.g. main()
//
namespace
{
  //--------------------------------------------------------------------------------
  // basic typedef and const
  const int ImageDimension = 3;

  typedef float FloatPixelType;
  typedef itk::Image<FloatPixelType, ImageDimension> FloatImageType;
  typedef FloatImageType ImageType;

  typedef short LabelPixelType;
  typedef itk::Image<LabelPixelType, ImageDimension> LabelImageType;

  //--------------------------------------------------------------------------------
  // functions
  //
  LabelImageType::Pointer computeOptimalPathLabelImage(ImageType::Pointer metricImage, LabelImageType::Pointer inputSeedLabelImage);

  // based on the center line label image and a set of points
  // (DIFFERNT FROM above where all points are along the same vessle,
  // here, each point belongs to a distinct branch), find the optimal
  // path back to the center axis.
  //
  // Yes, this way, we can't have complecated branches because there
  // is only one seed point on the branch and we want to trace back to
  // the main axis. This confines that the branch is relatively not
  // too curved.
  LabelImageType::Pointer computeBranchesFromAxisAndBranchSeedPoints(ImageType::Pointer metricImage, LabelImageType::Pointer axisLabelImage, const std::vector<std::vector<float> >& fiducialList);


  std::vector<std::vector<float> > findNewFiducialPoints(LabelImageType::Pointer axisLabelImage, const std::vector<std::vector<float> >& fiducialList);
}

int main( int argc, char * argv[] )
{
  PARSE_ARGS;

  //--------------------------------------------------------------------------------
  // read CT image
  typedef itk::ImageFileReader<ImageType>  ReaderType;
  ReaderType::Pointer reader = ReaderType::New();
  reader->SetFileName( inputVesselnessVolume.c_str() );
  reader->Update();
  ImageType::Pointer vesselnessMetricImage = reader->GetOutput();

  typedef itk::ImageFileReader<LabelImageType>  LabelReaderType;
  LabelReaderType::Pointer readerL = LabelReaderType::New();
  readerL->SetFileName( inputAxisLabelVolume.c_str() );
  readerL->Update();
  LabelImageType::Pointer caAxiaLabelImage = readerL->GetOutput();

  LabelImageType::Pointer axisLabelWithBranches = LabelImageType::New();

  // Segment branches
  if (!fiducialsOnBranches.empty())
    {
      std::vector<std::vector<float> > newFiducials = findNewFiducialPoints(caAxiaLabelImage, fiducialsOnBranches);

      std::cout<<"Totally "<<fiducialsOnBranches.size()<<" fiducials. "<<newFiducials.size()<<" new.\n";
      axisLabelWithBranches = computeBranchesFromAxisAndBranchSeedPoints(vesselnessMetricImage, caAxiaLabelImage, newFiducials);
    }


  //--------------------------------------------------------------------------------
  // write output
  typedef itk::ImageFileWriter<LabelImageType> WriterType;
  typename WriterType::Pointer writer = WriterType::New();
  writer->SetFileName( outputAxisAndBranchMaskVolume.c_str() );
  writer->SetInput( axisLabelWithBranches );
  writer->SetUseCompression(1);
  writer->Update();


  return EXIT_SUCCESS;
}

namespace
{
  std::vector<std::vector<float> > findNewFiducialPoints(LabelImageType::Pointer axisLabelImage, const std::vector<std::vector<float> >& fiducialList)
  {
    std::vector<std::vector<float> > newFiducialLPS;
    for( std::size_t i = 0; i < fiducialList.size(); i++ )
      {
        typename LabelImageType::PointType lpsPoint;
        lpsPoint[0] = fiducialList[i][0];
        lpsPoint[1] = fiducialList[i][1];
        lpsPoint[2] = fiducialList[i][2];
        typename LabelImageType::IndexType index;
        axisLabelImage->TransformPhysicalPointToIndex(lpsPoint, index);

        if (0 == axisLabelImage->GetPixel(index))
          {
            newFiducialLPS.push_back(fiducialList[i]);
          }
      }

    return newFiducialLPS;
  }

  LabelImageType::Pointer computeOptimalPathLabelImage(ImageType::Pointer metricImage, LabelImageType::Pointer inputSeedLabelImage)
  {
    //----------------------------------------------------------------------
    // Use short cut to find LCA axis
    gth818n::SeededOptimalPathFilter3D<ImageType, LabelImageType> sc;
    sc.SetSourceImage(metricImage);
    sc.SetSeedlImage(inputSeedLabelImage);

    // Do Segmentation
    sc.update();

    LabelImageType::Pointer optimalPathLabelImage = sc.GetBackTraceLabelImage();

    // typedef gth818n::SeededOptimalPathFilter3D<ImageType, LabelImageType>::FloatImageType FloatImageType;
    // FloatImageType::Pointer distanceImage = sc.GetDistanceImage();
    // gth818n::writeImage<FloatImageType>(distanceImage, "distanceMapLCA.nrrd", true);

    return optimalPathLabelImage;
  }

  LabelImageType::Pointer computeBranchesFromAxisAndBranchSeedPoints(ImageType::Pointer metricImage, LabelImageType::Pointer axisLabelImage, const std::vector<std::vector<float> >& fiducialList)
  {
    LabelImageType::Pointer seedLabelImageForBranch = LabelImageType::New();
    seedLabelImageForBranch->SetRegions(axisLabelImage->GetLargestPossibleRegion() );
    seedLabelImageForBranch->Allocate();
    seedLabelImageForBranch->CopyInformation(axisLabelImage);
    seedLabelImageForBranch->FillBuffer(0);

    const LabelImageType::PixelType* axisLabelImagePtr = axisLabelImage->GetBufferPointer();
    LabelImageType::PixelType* seedLabelImageForBranchPtr = seedLabelImageForBranch->GetBufferPointer();
    long np = axisLabelImage->GetLargestPossibleRegion().GetNumberOfPixels();

    for (long it = 0; it < np; ++it)
      {
        if (axisLabelImagePtr[it] != 0)
          {
            seedLabelImageForBranchPtr[it] = 1;
          }
      }

    for( std::size_t i = 0; i < fiducialList.size(); i++ )
      {
        typename LabelImageType::PointType lpsPointEnd;
        lpsPointEnd[0] = fiducialList[i][0];
        lpsPointEnd[1] = fiducialList[i][1];
        lpsPointEnd[2] = fiducialList[i][2];
        typename LabelImageType::IndexType indexEnd;
        metricImage->TransformPhysicalPointToIndex(lpsPointEnd, indexEnd);

        seedLabelImageForBranch->SetPixel(indexEnd, 2);
      }

    {
      typedef itk::ImageFileWriter<LabelImageType> WriterType;
      typename WriterType::Pointer writer = WriterType::New();
      writer->SetFileName( "axisLabelImage.nrrd" );
      writer->SetInput( axisLabelImage );
      writer->SetUseCompression(1);
      writer->Update();
    }

    {
      typedef itk::ImageFileWriter<LabelImageType> WriterType;
      typename WriterType::Pointer writer = WriterType::New();
      writer->SetFileName( "seedLabelImageForBranch.nrrd" );
      writer->SetInput( seedLabelImageForBranch );
      writer->SetUseCompression(1);
      writer->Update();
    }

    LabelImageType::Pointer axisWithBranches = computeOptimalPathLabelImage(metricImage, seedLabelImageForBranch);
    LabelImageType::PixelType* axisWithBranchesPtr = axisWithBranches->GetBufferPointer();

    for (long it = 0; it < np; ++it)
      {
        if (axisLabelImagePtr[it] != 0)
          {
            axisWithBranchesPtr[it] = axisLabelImagePtr[it];
          }

        if (axisWithBranchesPtr[it] != 0)
          {
            axisWithBranchesPtr[it] = 1;
          }
      }

    return axisWithBranches;
  }

}
