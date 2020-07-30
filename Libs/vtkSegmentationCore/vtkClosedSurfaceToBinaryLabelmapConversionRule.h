/*==============================================================================

  Copyright (c) Laboratory for Percutaneous Surgery (PerkLab)
  Queen's University, Kingston, ON, Canada. All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Csaba Pinter, PerkLab, Queen's University
  and was supported through the Applied Cancer Research Unit program of Cancer Care
  Ontario with funds provided by the Ontario Ministry of Health and Long-Term Care

==============================================================================*/

#ifndef __vtkClosedSurfaceToBinaryLabelmapConversionRule_h
#define __vtkClosedSurfaceToBinaryLabelmapConversionRule_h

// SegmentationCore includes
#include "vtkSegmentationConverterRule.h"
#include "vtkSegmentationConverter.h"

#include "vtkSegmentationCoreConfigure.h"

class vtkPolyData;

/// \ingroup SegmentationCore
/// \brief Convert closed surface representation (vtkPolyData type) to binary
///   labelmap representation (vtkOrientedImageData type). The conversion algorithm
///   is based on image stencil.
class vtkSegmentationCore_EXPORT vtkClosedSurfaceToBinaryLabelmapConversionRule
  : public vtkSegmentationConverterRule
{
public:
  /// Conversion parameter: oversampling factor
  /// Determines the oversampling of the reference image geometry. If it's a number, then all segments
  /// are oversampled with the same value (value of 1 means no oversampling). If it has the value "A",
  /// then automatic oversampling is calculated.
  static const std::string GetOversamplingFactorParameterName() { return "Oversampling factor"; };
  static const std::string GetCropToReferenceImageGeometryParameterName() { return "Crop to reference image geometry"; };

public:
  static vtkClosedSurfaceToBinaryLabelmapConversionRule* New();
  vtkTypeMacro(vtkClosedSurfaceToBinaryLabelmapConversionRule, vtkSegmentationConverterRule);
  virtual vtkSegmentationConverterRule* CreateRuleInstance();

  /// Constructs representation object from representation name for the supported representation classes
  /// (typically source and target representation VTK classes, subclasses of vtkDataObject)
  /// Note: Need to take ownership of the created object! For example using vtkSmartPointer<vtkDataObject>::Take
  virtual vtkDataObject* ConstructRepresentationObjectByRepresentation(std::string representationName);

  /// Constructs representation object from class name for the supported representation classes
  /// (typically source and target representation VTK classes, subclasses of vtkDataObject)
  /// Note: Need to take ownership of the created object! For example using vtkSmartPointer<vtkDataObject>::Take
  virtual vtkDataObject* ConstructRepresentationObjectByClass(std::string className);

  /// Update the target representation based on the source representation
  virtual bool Convert(vtkDataObject* sourceRepresentation, vtkDataObject* targetRepresentation);

  /// Get the cost of the conversion.
  virtual unsigned int GetConversionCost(vtkDataObject* sourceRepresentation=NULL, vtkDataObject* targetRepresentation=NULL);

  /// Human-readable name of the converter rule
  virtual const char* GetName() { return "Closed surface to binary labelmap (simple image stencil)"; };

  /// Human-readable name of the source representation
  virtual const char* GetSourceRepresentationName() { return vtkSegmentationConverter::GetSegmentationClosedSurfaceRepresentationName(); };

  /// Human-readable name of the target representation
  virtual const char* GetTargetRepresentationName() { return vtkSegmentationConverter::GetSegmentationBinaryLabelmapRepresentationName(); };

  vtkSetMacro(UseOutputImageDataGeometry, bool);

protected:
  /// Calculate actual geometry of the output labelmap volume by verifying that the reference image geometry
  /// encompasses the input surface model, and extending it to the proper directions if necessary.
  /// \param closedSurfacePolyData Input closed surface poly data to convert
  /// \param geometryImageData Output dummy image data containing output labelmap geometry
  /// \return Success flag indicating sane calculated extents
  bool CalculateOutputGeometry(vtkPolyData* closedSurfacePolyData, vtkOrientedImageData* geometryImageData);

  /// Get default image geometry string in case of absence of parameter.
  /// The default geometry has identity directions and 1 mm uniform spacing,
  /// with origin and extent defined using the argument poly data.
  /// \param polyData Poly data defining the origin and extent of the default geometry
  /// \return Serialized image geometry for input poly data with identity directions and 1 mm spacing.
  std::string GetDefaultImageGeometryStringForPolyData(vtkPolyData* polyData);

protected:
  /// Flag determining whether to use the geometry of the given output oriented image data as is,
  /// or use the conversion parameters and the extent of the input surface. False by default,
  /// because pre-calculating the geometry of the output image data is not trivial and should be done
  /// only when there is a specific reason to do that (such as doing the conversion for sub-volumes and
  /// then stitching them back together).
  bool UseOutputImageDataGeometry;

protected:
  vtkClosedSurfaceToBinaryLabelmapConversionRule();
  ~vtkClosedSurfaceToBinaryLabelmapConversionRule();
  void operator=(const vtkClosedSurfaceToBinaryLabelmapConversionRule&);
};

#endif // __vtkClosedSurfaceToBinaryLabelmapConversionRule_h