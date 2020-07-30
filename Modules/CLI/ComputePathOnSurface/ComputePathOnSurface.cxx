#include <algorithm>

#include <omp.h>

#include "SeededOptimalPathFilter3D.h"
#include "ShortCutFilter3D.h"

#include "itkBinaryDilateImageFilter.h"
#include "itkBinaryBallStructuringElement.h"

#include "itkImageRegionIterator.h"
#include "itkHessian3DToVesselnessMeasureImageFilter.h"
#include "itkHessianRecursiveGaussianImageFilter.h"

#include "itkImageFileWriter.h"

#include "itkPluginUtilities.h"

#include "ComputePathOnSurfaceCLP.h"


#include "vtkSmartPointer.h"
#include "vtkXMLPolyDataWriter.h"
#include "vtkXMLPolyDataReader.h"
#include "vtkPolyData.h"

#include <vtkProperty.h>
#include <vtkPolyData.h>
// #include <vtkPolyDataMapper.h>
// #include <vtkActor.h>
// #include <vtkRenderWindow.h>
// #include <vtkRenderer.h>
// #include <vtkRenderWindowInteractor.h>
#include <vtkDijkstraGraphGeodesicPath.h>
#include <vtkTriangleFilter.h>

//#include "vtkCellLocator.h"
#include "vtkKdTreePointLocator.h"
#include "vtkPolyLine.h"

#include "vtkAppendPolyData.h"


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
}

int main( int argc, char * argv[] )
{
  PARSE_ARGS;

  std::cout<<ModelSceneFile<<std::endl;
  std::cout<<"I'm in"<<std::endl<<std::flush;
  std::cout<<fiducialsAlongCA.size()<<std::endl<<std::flush;
  std::cout<<fiducialsAlongCA[0][0]<<", "<<fiducialsAlongCA[0][1]<<", "<<fiducialsAlongCA[0][2]<<std::endl;
  //std::cout<<fiducialsAlongCA[fiducialsAlongCA.size()-1][0]<<", "<<fiducialsAlongCA[fiducialsAlongCA.size()-1][1]<<", "<<fiducialsAlongCA[fiducialsAlongCA.size()-1][2]<<std::endl;

  std::cout<<"I'm in"<<std::endl<<std::flush;


  //--------------------------------------------------------------------------------
  // read CT image
  // read in polydata
  vtkSmartPointer<vtkXMLPolyDataReader> reader = vtkSmartPointer<vtkXMLPolyDataReader>::New();
  reader->SetFileName( ModelSceneFile.c_str());
  reader->Update();

  vtkSmartPointer<vtkPolyData> polyData1 = reader->GetOutput();

  // this triangulation is a must. without which won't work
  vtkSmartPointer<vtkTriangleFilter> triangleFilter = vtkSmartPointer<vtkTriangleFilter>::New();
  triangleFilter->SetInputData( polyData1 );
  triangleFilter->Update();
  vtkSmartPointer<vtkPolyData> polyData = triangleFilter->GetOutput();

  std::cout<<"polyData has number of points: "<<polyData->GetNumberOfPoints()<<std::endl<<std::flush;
  //std::cout<<"polyData1 has number of points: "<<polyData1->GetNumberOfPoints()<<std::endl;

  double rootPoint[3] = {fiducialsAlongCA[0][0], fiducialsAlongCA[0][1], fiducialsAlongCA[0][2]};

  vtkSmartPointer<vtkKdTreePointLocator> kDTree = vtkSmartPointer<vtkKdTreePointLocator>::New();
  kDTree->SetDataSet(polyData);
  kDTree->BuildLocator();
  vtkIdType closestPointInPdRoot = kDTree->FindClosestPoint(rootPoint);


  vtkSmartPointer<vtkPolyData> axisPolyData = vtkSmartPointer<vtkPolyData>::New();

  for (size_t itStartingPoint = 1; itStartingPoint < fiducialsAlongCA.size(); ++itStartingPoint)
    {
      double startPoint[3] = {fiducialsAlongCA[itStartingPoint][0], \
                              fiducialsAlongCA[itStartingPoint][1], \
                              fiducialsAlongCA[itStartingPoint][2]};

      std::cout<<"Tracing point id: "<<itStartingPoint<<std::endl;
      std::cout<<"Root: "<<rootPoint[0]<<", "<<rootPoint[1]<<", "<<rootPoint[2]<<std::endl;
      std::cout<<"start: "<<startPoint[0]<<", "<<startPoint[1]<<", "<<startPoint[2]<<std::endl<<std::flush;

      vtkIdType closestPointInPdStart = kDTree->FindClosestPoint(startPoint);

      std::cout << "Root and Start: " << closestPointInPdStart<<", "<< closestPointInPdRoot<< std::endl;

      vtkSmartPointer<vtkDijkstraGraphGeodesicPath> dijkstra = vtkSmartPointer<vtkDijkstraGraphGeodesicPath>::New();
      dijkstra->SetInputData(polyData);
      dijkstra->SetStartVertex(closestPointInPdStart);
      dijkstra->SetEndVertex(closestPointInPdRoot);
      dijkstra->Update();

      vtkSmartPointer<vtkIdList> poitnsOnPath = dijkstra->GetIdList();

      for (vtkIdType it = 0; it < poitnsOnPath->GetNumberOfIds(); ++it)
        {
          vtkIdType thisId = poitnsOnPath->GetId(it);
          std::cout<<thisId<<", ";
        }
      std::cout<<std::endl;


      //--------------------------------------------------------------------------------
      // make a line from the points
      // Create a vtkPoints container and store the points in it
      vtkSmartPointer<vtkPoints> pts = vtkSmartPointer<vtkPoints>::New();
      double pt[3];

      for (vtkIdType it = 0; it < poitnsOnPath->GetNumberOfIds(); ++it)
        {
          vtkIdType thisId = poitnsOnPath->GetId(it);
          polyData->GetPoint(thisId, pt);

          pts->InsertNextPoint(pt);
        }

      vtkSmartPointer<vtkPolyLine> polyLine = vtkSmartPointer<vtkPolyLine>::New();
      polyLine->GetPointIds()->SetNumberOfIds(poitnsOnPath->GetNumberOfIds());
      for(unsigned int i = 0; i < poitnsOnPath->GetNumberOfIds(); i++)
        {
          polyLine->GetPointIds()->SetId(i,i);
        }

      // Create a cell array to store the lines in and add the lines to it
      vtkSmartPointer<vtkCellArray> cells = vtkSmartPointer<vtkCellArray>::New();
      cells->InsertNextCell(polyLine);

      vtkSmartPointer<vtkPolyData> thisPolyData = vtkSmartPointer<vtkPolyData>::New();
      // Add the points to the dataset
      thisPolyData->SetPoints(pts);
      // Add the lines to the dataset
      thisPolyData->SetLines(cells);


      vtkSmartPointer<vtkAppendPolyData> appender = vtkSmartPointer<vtkAppendPolyData>::New();
      appender->AddInputData(axisPolyData);
      appender->AddInputData(thisPolyData);
      appender->Update();

      axisPolyData = appender->GetOutput();
    }

  vtkSmartPointer<vtkXMLPolyDataWriter> writer = vtkSmartPointer<vtkXMLPolyDataWriter>::New();
  writer->SetFileName(axisPolylineName.c_str());
  writer->SetInputData(axisPolyData);

  // Optional - set the mode. The default is binary.
  //writer->SetDataModeToBinary();
  writer->SetDataModeToAscii();

  writer->Write();


  return EXIT_SUCCESS;
}

namespace
{

}
