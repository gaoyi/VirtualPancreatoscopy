import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np

#
# CoronaryArteryAnalysis
#

class CoronaryArteryAnalysis(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "CoronaryArteryAnalysis" # TODO make this more human readable by adding spaces
    self.parent.categories = ["CoronaryArtery"]
    self.parent.dependencies = []
    self.parent.contributors = ["Yi Gao"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an extension for coronary artery analysis.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# CoronaryArteryAnalysisWidget
#

class CoronaryArteryAnalysisWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent = None):
    ScriptedLoadableModuleWidget.__init__(self, parent) # must have this. otherwise get error when loading this module

    # self.originalVolumeNode = None
    # self.vesselnessVolumeNode = None
    # self.axisLabelVolumeNode = None
    # self.mainAndBranchAxisLabelImageNode = None
  

    
    #--------------------------------------------------------------------------------
    # Copy Endoscopy

    self.cameraNode = None
    self.cameraNodeObserverTag = None
    self.cameraObserverTag= None
    # Flythough variables
    self.transform = None
    self.path = None
    self.camera = None
    self.skip = 0
    self.timer = qt.QTimer()
    self.timer.setInterval(20)
    self.timer.connect('timeout()', self.flyToNext)

    #================================================================================



  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...
    self.setupWholePanel()

    #--------------------------------------------------------------------------------
    # Add vertical spacer
    #self.layout.addStretch(1)

    # Refresh Apply button state
    #self.enableOrDisableComputeVesslenessButton()


    
    #--------------------------------------------------------------------------------
    #
    # Copy Endoscopy
    #

    # Path collapsible button
    pathCollapsibleButton = ctk.ctkCollapsibleButton()
    pathCollapsibleButton.text = "Path"
    # pathCollapsibleButton.enabled = False
    self.layout.addWidget(pathCollapsibleButton)

    # Layout within the path collapsible button
    pathFormLayout = qt.QFormLayout(pathCollapsibleButton)

    # Camera node selector
    cameraNodeSelector = slicer.qMRMLNodeComboBox()
    cameraNodeSelector.objectName = 'cameraNodeSelector'
    cameraNodeSelector.toolTip = "Select a camera that will fly along this path."
    cameraNodeSelector.nodeTypes = ['vtkMRMLCameraNode']
    cameraNodeSelector.noneEnabled = False
    cameraNodeSelector.addEnabled = False
    cameraNodeSelector.removeEnabled = False
    cameraNodeSelector.connect('currentNodeChanged(bool)', self.enableOrDisableCreateButton)
    cameraNodeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.setCameraNode)
    pathFormLayout.addRow("Camera:", cameraNodeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        cameraNodeSelector, 'setMRMLScene(vtkMRMLScene*)')

    # Input fiducials node selector
    inputFiducialsNodeSelector = slicer.qMRMLNodeComboBox()
    inputFiducialsNodeSelector.objectName = 'inputFiducialsNodeSelector'
    inputFiducialsNodeSelector.toolTip = "Select a fiducial list to define control points for the path."
    inputFiducialsNodeSelector.nodeTypes = ['vtkMRMLMarkupsFiducialNode', 'vtkMRMLAnnotationHierarchyNode', 'vtkMRMLFiducialListNode']
    inputFiducialsNodeSelector.noneEnabled = False
    inputFiducialsNodeSelector.addEnabled = False
    inputFiducialsNodeSelector.removeEnabled = False
    inputFiducialsNodeSelector.connect('currentNodeChanged(bool)', self.enableOrDisableCreateButton)
    pathFormLayout.addRow("Input Fiducials:", inputFiducialsNodeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        inputFiducialsNodeSelector, 'setMRMLScene(vtkMRMLScene*)')

    # CreatePath button
    createPathButton = qt.QPushButton("Create path")
    createPathButton.toolTip = "Create the path."
    createPathButton.enabled = False
    pathFormLayout.addRow(createPathButton)
    createPathButton.connect('clicked()', self.onCreatePathButtonClicked)


    # Flythrough collapsible button
    flythroughCollapsibleButton = ctk.ctkCollapsibleButton()
    flythroughCollapsibleButton.text = "Flythrough"
    flythroughCollapsibleButton.enabled = False
    self.layout.addWidget(flythroughCollapsibleButton)

    # Layout within the Flythrough collapsible button
    flythroughFormLayout = qt.QFormLayout(flythroughCollapsibleButton)

    # Frame slider
    frameSlider = ctk.ctkSliderWidget()
    frameSlider.connect('valueChanged(double)', self.frameSliderValueChanged)
    frameSlider.decimals = 0
    flythroughFormLayout.addRow("Frame:", frameSlider)

    # Frame skip slider
    frameSkipSlider = ctk.ctkSliderWidget()
    frameSkipSlider.connect('valueChanged(double)', self.frameSkipSliderValueChanged)
    frameSkipSlider.decimals = 0
    frameSkipSlider.minimum = 0
    frameSkipSlider.maximum = 10
    flythroughFormLayout.addRow("Frame skip:", frameSkipSlider)

    # Frame delay slider
    frameDelaySlider = ctk.ctkSliderWidget()
    frameDelaySlider.connect('valueChanged(double)', self.frameDelaySliderValueChanged)
    frameDelaySlider.decimals = 0
    frameDelaySlider.minimum = 5
    frameDelaySlider.maximum = 100
    frameDelaySlider.suffix = " ms"
    frameDelaySlider.value = 20
    flythroughFormLayout.addRow("Frame delay:", frameDelaySlider)

    # View angle slider
    viewAngleSlider = ctk.ctkSliderWidget()
    viewAngleSlider.connect('valueChanged(double)', self.viewAngleSliderValueChanged)
    viewAngleSlider.decimals = 0
    viewAngleSlider.minimum = 30
    viewAngleSlider.maximum = 180
    flythroughFormLayout.addRow("View Angle:", viewAngleSlider)

    # Play button
    playButton = qt.QPushButton("Play")
    playButton.toolTip = "Fly through path."
    playButton.checkable = True
    flythroughFormLayout.addRow(playButton)
    playButton.connect('toggled(bool)', self.onPlayButtonToggled)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Set local var as instance attribute
    self.cameraNodeSelector = cameraNodeSelector
    self.inputFiducialsNodeSelector = inputFiducialsNodeSelector
    self.createPathButton = createPathButton
    self.flythroughCollapsibleButton = flythroughCollapsibleButton
    self.frameSlider = frameSlider
    self.viewAngleSlider = viewAngleSlider
    self.playButton = playButton

    cameraNodeSelector.setMRMLScene(slicer.mrmlScene)
    inputFiducialsNodeSelector.setMRMLScene(slicer.mrmlScene)
    
    #
    # Copy Endoscopy
    #
    #================================================================================



  def onComputeLumenButton(self):
    originalVolumeNode = self.inputOriginalImageSelector1.currentNode()
    inputAxisLabelNode = self.inputAxisLabelImageSelector2.currentNode()
    outputLumenLabelVolumeNode = self.outputLumenLabelImageSelector.currentNode()


    # run the filter
    ijkToRAS = vtk.vtkMatrix4x4()
    originalVolumeNode.GetIJKToRASMatrix(ijkToRAS)
    outputLumenLabelVolumeNode.SetIJKToRASMatrix(ijkToRAS)
    #outputLumenLabelVolumeNode.SetName("vesselLumenLabelVolume")

    parameters = {}
    parameters['inputVolume'] = originalVolumeNode.GetID()
    parameters['inputAxisLabelVolume'] = inputAxisLabelNode.GetID()
    parameters['lowerThreshold'] = self.thresholdSliderWidget.value
    parameters['outputLumenMaskVolume'] = outputLumenLabelVolumeNode.GetID()

    slicer.cli.run( slicer.modules.segmentlumenfromaxis, None, parameters, wait_for_completion=True )


  def setupWholePanel(self):
    wholeProcessCollapsibleButton = ctk.ctkCollapsibleButton()
    wholeProcessCollapsibleButton.text = "The Whole Process Pipeline"
    self.layout.addWidget(wholeProcessCollapsibleButton)

    # Layout within the dummy collapsible button
    wholeProcessFormLayout = qt.QFormLayout(wholeProcessCollapsibleButton)

    #
    # input volume selector
    #
    self.inputOriginalImageSelector = slicer.qMRMLNodeComboBox()
    self.inputOriginalImageSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputOriginalImageSelector.selectNodeUponCreation = True
    self.inputOriginalImageSelector.addEnabled = False
    self.inputOriginalImageSelector.removeEnabled = False
    self.inputOriginalImageSelector.renameEnabled = False
    self.inputOriginalImageSelector.noneEnabled = False
    self.inputOriginalImageSelector.showHidden = False
    self.inputOriginalImageSelector.showChildNodeTypes = False
    self.inputOriginalImageSelector.setMRMLScene( slicer.mrmlScene )
    self.inputOriginalImageSelector.setToolTip( "Pick the input to the algorithm." )
    wholeProcessFormLayout.addRow("Input Volume: ", self.inputOriginalImageSelector)

    # Input fiducials node selector
    self.treeFiducialsNodeSelector = slicer.qMRMLNodeComboBox()
    self.treeFiducialsNodeSelector.objectName = 'treeFiducialsNodeSelector'
    self.treeFiducialsNodeSelector.toolTip = "Select a fiducial list to define control points for the axis."
    self.treeFiducialsNodeSelector.nodeTypes = ['vtkMRMLMarkupsFiducialNode', 'vtkMRMLAnnotationHierarchyNode', 'vtkMRMLFiducialListNode']
    #self.treeFiducialsNodeSelector.nodeTypes = ['vtkMRMLMarkupsFiducialNode']
    self.treeFiducialsNodeSelector.noneEnabled = False
    self.treeFiducialsNodeSelector.renameEnabled = False
    self.treeFiducialsNodeSelector.addEnabled = False
    self.treeFiducialsNodeSelector.removeEnabled = False
    wholeProcessFormLayout.addRow("Axis Tree Fiducials:", self.treeFiducialsNodeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.treeFiducialsNodeSelector, 'setMRMLScene(vtkMRMLScene*)') #not sure what this line is for???

    #
    # output lumen label image selector
    #
    self.outputLumenLabelImageSelector = slicer.qMRMLNodeComboBox()
    self.outputLumenLabelImageSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.outputLumenLabelImageSelector.objectName = "lumenLabelVolume"
    self.outputLumenLabelImageSelector.selectNodeUponCreation = True
    self.outputLumenLabelImageSelector.renameEnabled = True
    self.outputLumenLabelImageSelector.addEnabled = True
    self.outputLumenLabelImageSelector.removeEnabled = False
    self.outputLumenLabelImageSelector.noneEnabled = False
    self.outputLumenLabelImageSelector.showHidden = False
    self.outputLumenLabelImageSelector.showChildNodeTypes = False
    self.outputLumenLabelImageSelector.setMRMLScene( slicer.mrmlScene )
    self.outputLumenLabelImageSelector.setToolTip( "Pick the output to the algorithm." )
    wholeProcessFormLayout.addRow("Lumen Label Volume: ", self.outputLumenLabelImageSelector)


    self.vesselBrighterCheckBox = qt.QCheckBox()
    self.vesselBrighterCheckBox.checked = False
    self.vesselBrighterCheckBox.setToolTip("Is vessel brighter than the surroundings?")
    wholeProcessFormLayout.addRow("Vessel brighter than the surroundings?", self.vesselBrighterCheckBox)

    #
    # Calcification threshold
    #
    self.calcificationSlicerWidget = ctk.ctkSliderWidget()
    self.calcificationSlicerWidget.singleStep = 1
    self.calcificationSlicerWidget.minimum = -1000
    self.calcificationSlicerWidget.maximum = 10000
    self.calcificationSlicerWidget.value = 800
    self.calcificationSlicerWidget.setToolTip("Calcification value.")
    wholeProcessFormLayout.addRow("Calcification", self.calcificationSlicerWidget)


    self.thresholdSliderWidget = ctk.ctkSliderWidget()
    self.thresholdSliderWidget.tracking = True
    self.thresholdSliderWidget.singleStep = 1
    self.thresholdSliderWidget.minimum = -1000
    self.thresholdSliderWidget.maximum = 1000
    self.thresholdSliderWidget.decimals = 0
    self.thresholdSliderWidget.value = 0
    self.thresholdSliderWidget.setToolTip("Threshold Value")
    self.thresholdSliderWidget.enabled = True
    wholeProcessFormLayout.addRow("Treshold", self.thresholdSliderWidget)

    self.superResolutionCheckBox = qt.QCheckBox()
    self.superResolutionCheckBox.checked = False
    self.superResolutionCheckBox.setToolTip("Perform super-resolution segmentation?")
    wholeProcessFormLayout.addRow("Perform super-resolution segmentation?", self.superResolutionCheckBox)

    #
    # Apply Button
    #
    self.computeWholeProcess = qt.QPushButton("Run it")
    self.computeWholeProcess.toolTip = "Run the whole process."
    self.computeWholeProcess.enabled = True
    wholeProcessFormLayout.addRow(self.computeWholeProcess)

    # connections
    self.computeWholeProcess.connect('clicked(bool)', self.onWholeProcessButton)

  def cleanup(self):
    pass


  def enableOrDisableComputeVesslenessButton(self):
    self.computeVesslenessButton.enabled = self.inputOriginalImageSelector.currentNodeID and self.outputVesslenessImageSelector.currentNodeID


  def onWholeProcessButton(self):
    #--------------------------------------------------------------------------------
    # Run the ComputeVesselness CLI to get the vesselness
    parameters = {}
    parameters['inputVolume'] = self.inputOriginalImageSelector.currentNode().GetID()
    parameters['vesselIsBrighter'] = self.vesselBrighterCheckBox.checked
    vesselNessImageNode = slicer.vtkMRMLScalarVolumeNode()
    vesselNessImageNode.SetName("vesselNessImage")
    slicer.mrmlScene.AddNode( vesselNessImageNode )
    parameters['outputVesselnessVolume'] = vesselNessImageNode.GetID()
    parameters['sigma'] = 1.0
    parameters['alpha1'] = 2.0
    parameters['alpha2'] = 2.0
    parameters['calcificationThreshold'] = self.calcificationSlicerWidget.value
    slicer.cli.run( slicer.modules.computevesselness, None, parameters, wait_for_completion=True )
    # Run the ComputeVesselness CLI to get the vesselness
    #================================================================================


    #--------------------------------------------------------------------------------
    # Compute axis tree
    parameters = {}
    parameters['inputVesselnessVolume'] = vesselNessImageNode.GetID()
    parameters['fiducialsAlongCA'] = self.treeFiducialsNodeSelector.currentNode()

    axisTreeLabelImageNode = slicer.vtkMRMLLabelMapVolumeNode()
    axisTreeLabelImageNode.SetName("axisTreeLabelImage")
    slicer.mrmlScene.AddNode( axisTreeLabelImageNode )
    parameters['outputAxisMaskVolume'] = axisTreeLabelImageNode.GetID()

    ################################################################################
    # This CLI module "computetree" treat the 1st fiducial point as
    #the root and trace every other fiducial points back to the root
    #slicer.cli.run( slicer.modules.computetree, None, parameters, wait_for_completion=True )

    ################################################################################
    # This CLI module "ComputeAxisFromVesselness" treat the (i-1)-th
    #fiducial point as the root and trace from the i-th point to the
    #(i-1)-th one. Then from (i+1) to i, and on. So this module gives
    #a SINGEL axis.
    #slicer.cli.run( slicer.modules.ComputeAxisFromVesselness, None, parameters, wait_for_completion=True )
    slicer.cli.run( slicer.modules.computeaxisfromvesselness, None, parameters, wait_for_completion=True )
    #================================================================================

    #--------------------------------------------------------------------------------
    # Run the SegmentLumenFromAxis CLI to get the vesselness
    parameters = {}
    parameters['inputVolume'] = self.inputOriginalImageSelector.currentNode().GetID()
    parameters['inputAxisLabelVolume'] = axisTreeLabelImageNode.GetID()
    parameters['lowerThreshold'] = self.thresholdSliderWidget.value
    parameters['calcificationThreshold'] = self.calcificationSlicerWidget.value
    parameters['outputLumenMaskVolume'] = self.outputLumenLabelImageSelector.currentNode()
    parameters['superResolution'] = self.superResolutionCheckBox.checked

    slicer.cli.run( slicer.modules.segmentlumenfromaxis, None, parameters, wait_for_completion=True )
    # Run the SegmentLumenFromAxis CLI to get the vesselness
    #================================================================================

    d = vesselNessImageNode.GetDisplayNode()
    d.SetVisibility(0) # do not show the vesselness image





    
    #--------------------------------------------------------------------------------
    # Run the model maker to genreate surface
    parameters = {}
    parameters['InputVolume'] = self.outputLumenLabelImageSelector.currentNode().GetID()
    lumenModelHierarchy = slicer.vtkMRMLModelHierarchyNode()
    lumenModelHierarchy.SetName("theLumenModelHierarchy")
    slicer.mrmlScene.AddNode( lumenModelHierarchy )
    parameters['ModelSceneFile'] = lumenModelHierarchy.GetID()
    slicer.cli.run( slicer.modules.modelmaker, None, parameters, wait_for_completion=True )
    # Run the model maker to genreate surface
    #================================================================================



    #--------------------------------------------------------------------------------
    # Backface To Frontface 
    e = slicer.util.getNode('Model_1_jake')
    f = e.GetDisplayNode()
    f.SetBackfaceCulling(0)
    f.SetFrontfaceCulling(1)
    # Backface To Frontface 
    #================================================================================



    #--------------------------------------------------------------------------------
    # To get the central coordinates of pancreatic duct and insert fiducials on them
    inputvalues = slicer.util.getNode('axisTreeLabelImage')
    # print 'ehhhhh.'
    # print inputvalues
    inputdata = slicer.util.arrayFromVolume(inputvalues)
    coordinates = np.where(inputdata != 0)
    I = coordinates[2][3::3]
    # print 'I:'
    # print I
    J = coordinates[1][3::3]
    # print 'J:'
    # print J
    K = coordinates[0][3::3]
    # print 'K:'
    # print K
    RasCoordinates = []
    N = 0
    
    # IJK TO RAS
    ijkToRasMatrix = vtk.vtkMatrix4x4()
    inputvalues.GetIJKToRASMatrix(ijkToRasMatrix)	
    for N in range(len(I)):
      c_Ijk = [I[N],J[N],K[N],1]
      c_Ras = ijkToRasMatrix.MultiplyFloatPoint(c_Ijk)
      RasCoordinates.append(c_Ras)
    # print 'RasCoordinates:'
    # print RasCoordinates

    # Change the bottom fiducial point to the second point
    fidNode = slicer.util.getNode('F')
    ras = [0,0,0]
    fidNode.GetNthFiducialPosition(1,ras)
    # print(ras)
    RasCoordinates.append(ras)
    fidNode.SetNthFiducialPosition(1,RasCoordinates[0][0],RasCoordinates[0][1],RasCoordinates[0][2])
    RasCoordinates.pop(0)
    for c in RasCoordinates:
      slicer.modules.markups.logic().AddFiducial(c[0],c[1],c[2])
    # To get the central coordinates of pancreatic duct and insert fiducials on them
    #================================================================================
   




    # TODO
    # parameters = {}
    # parameters["InputVolume"] = vesselNessImage.GetID()
    # grayModel = slicer.vtkMRMLModelNode()
    # slicer.mrmlScene.AddNode( grayModel )
    # parameters["OutputGeometry"] = grayModel.GetID()
    # parameters['Threshold'] = self.vesselSlicerWidget.value
    # grayMaker = slicer.modules.grayscalemodelmaker
    # slicer.cli.runSync(grayMaker, None, parameters)
    # d = grayModel.GetDisplayNode()
    # d.SetVisibility(0) # do not show the gray model


    # parameters = {}
    # parameters["ModelSceneFile"] = grayModel.GetID()
    # parameters["fiducialsAlongCA"] = self.axisFiducialsNodeSelectorNew.currentNode().GetID()
    # parameters["axisPolylineName"] = self.outputGeometrySelector.currentNode().GetID()
    # slicer.cli.run( slicer.modules.computepathonsurface, None, parameters, wait_for_completion=True )

  def onNewButton(self):

    parameters = {}
    parameters['inputVolume'] = self.inputOriginalImageSelector.currentNode().GetID()
    parameters['vesselIsBrighter'] = self.vesselBrighterCheckBox.checked
    vesselNessImage = slicer.vtkMRMLScalarVolumeNode()
    vesselNessImage.SetName("vesselNessImage")
    slicer.mrmlScene.AddNode( vesselNessImage )
    parameters['outputVesselnessVolume'] = vesselNessImage.GetID()
    parameters['sigma'] = 1.0
    parameters['alpha1'] = 2.0
    parameters['alpha2'] = 2.0
    parameters['calcificationThreshold'] = self.calcificationSlicerWidget.value
    slicer.cli.run( slicer.modules.computevesselness, None, parameters, wait_for_completion=True )

    parameters = {}
    parameters["InputVolume"] = vesselNessImage.GetID()
    grayModel = slicer.vtkMRMLModelNode()
    slicer.mrmlScene.AddNode( grayModel )
    parameters["OutputGeometry"] = grayModel.GetID()
    parameters['Threshold'] = self.vesselSlicerWidget.value
    grayMaker = slicer.modules.grayscalemodelmaker
    slicer.cli.runSync(grayMaker, None, parameters)
    d = grayModel.GetDisplayNode()
    d.SetVisibility(0) # do not show the gray model


    parameters = {}
    parameters["ModelSceneFile"] = grayModel.GetID()
    parameters["fiducialsAlongCA"] = self.axisFiducialsNodeSelectorNew.currentNode().GetID()
    parameters["axisPolylineName"] = self.outputGeometrySelector.currentNode().GetID()
    slicer.cli.run( slicer.modules.computepathonsurface, None, parameters, wait_for_completion=True )


  def onComputeBranchButton(self):
    vesselnessVolumeNode = self.inputVesslenessImageSelector2.currentNode()
    inputAxisLabelNode = self.inputAxisLabelImageSelector1.currentNode()
    mainAndBranchAxisLabelImageNode = self.outputBranchLabelImageSelector.currentNode()
    #self.mainAndBranchAxisLabelImageNode.SetName("axisWithBranchLabelVolume-label")
    if not (vesselnessVolumeNode and mainAndBranchAxisLabelImageNode):
      qt.QMessageBox.critical(
        slicer.util.mainWindow(),
        'Compute', 'Input and output volumes are required for computing branch axis')
      return
    # run the filter
    ijkToRAS = vtk.vtkMatrix4x4()
    vesselnessVolumeNode.GetIJKToRASMatrix(ijkToRAS)
    mainAndBranchAxisLabelImageNode.SetIJKToRASMatrix(ijkToRAS)

    branchFiducialsNode = self.branchFiducialsNodeSelector.currentNode();

    parameters = {}
    parameters['inputVesselnessVolume'] = vesselnessVolumeNode.GetID()
    parameters['fiducialsOnBranches'] = branchFiducialsNode.GetID()
    parameters['inputAxisLabelVolume'] = inputAxisLabelNode.GetID()
    parameters['outputAxisAndBranchMaskVolume'] = mainAndBranchAxisLabelImageNode.GetID()

    slicer.cli.run( slicer.modules.computebranchaxis, None, parameters, wait_for_completion=True )

  def onPreProcessImageButton(self):
    originalVolumeNode = self.inputOriginalImageSelector.currentNode()
    vesselnessVolumeNode = self.outputVesslenessImageSelector.currentNode()
    #vesselnessVolumeNode.SetName("vesselnessVolume")
    if not (originalVolumeNode and vesselnessVolumeNode):
      qt.QMessageBox.critical(
          slicer.util.mainWindow(),
          'Compute', 'Input and output volumes are required for computing vessleness')
      return
    # run the filter
    ijkToRAS = vtk.vtkMatrix4x4()
    originalVolumeNode.GetIJKToRASMatrix(ijkToRAS)
    vesselnessVolumeNode.SetIJKToRASMatrix(ijkToRAS)

    parameters = {}
    parameters['inputVolume'] = originalVolumeNode.GetID()
    parameters['vesselIsBrighter'] = self.vesselBrighterCheckBox.checked
    parameters['outputVesselnessVolume'] = vesselnessVolumeNode.GetID()
    parameters['sigma'] = 0.5
    parameters['alpha1'] = 0.5
    parameters['alpha2'] = 2.0
    parameters['calcificationThreshold'] = self.calcificationSlicerWidget.value
    # parameters['sigma'] = self.sigmaSlicerWidget.value
    # parameters['alpha1'] = self.alpha1SlicerWidget.value
    # parameters['alpha2'] = self.alpha2SlicerWidget.value

    slicer.cli.run( slicer.modules.computevesselness, None, parameters, wait_for_completion=True )


    # fill computed vesselness image to other UI selectors
    self.inputVesslenessImageSelector1.setCurrentNode(self.outputVesslenessImageSelector.currentNode());
    self.inputVesslenessImageSelector2.setCurrentNode(self.outputVesslenessImageSelector.currentNode());


    appLogic = slicer.app.applicationLogic()
    selectionNode = appLogic.GetSelectionNode()
    selectionNode.SetReferenceActiveVolumeID(self.inputOriginalImageSelector.currentNode().GetID())
    #selectionNode.SetReferenceSecondaryVolumeID(fg)
    appLogic.PropagateVolumeSelection()

#    self.computeAxisButton.enabled = True



  def onComputeAxisButton(self):
    inputVesselnessVolumeNode = self.inputVesslenessImageSelector1.currentNode()
    axisLabelVolumeNode = self.outputAxisLabelImageSelector.currentNode()
    #self.axisLabelVolumeNode.SetName("axisLabelVolume-label")
    if not (inputVesselnessVolumeNode and axisLabelVolumeNode):
      qt.QMessageBox.critical(
        slicer.util.mainWindow(),
        'Compute', 'Input and output volumes are required for computing axis')
      return
    # run the filter
    ijkToRAS = vtk.vtkMatrix4x4()
    inputVesselnessVolumeNode.GetIJKToRASMatrix(ijkToRAS)
    axisLabelVolumeNode.SetIJKToRASMatrix(ijkToRAS)

    axisFiducialsNode = self.axisFiducialsNodeSelector.currentNode();

    parameters = {}
    parameters['inputVesselnessVolume'] = inputVesselnessVolumeNode.GetID()
    parameters['fiducialsAlongCA'] = axisFiducialsNode.GetID()
    parameters['outputAxisMaskVolume'] = axisLabelVolumeNode.GetID()


    slicer.cli.run( slicer.modules.computeaxisfromvesselness, None, parameters, wait_for_completion=True )

    # logic = CoronaryArteryAnalysisLogic()
    # enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    # imageThreshold = self.sigmaSlicerWidget.value
    # logic.run(self.inputOriginalImageSelector.currentNode(), self.outputAxisLabelImageSelector.currentNode(), imageThreshold, enableScreenshotsFlag)

#
# CoronaryArteryAnalysisLogic
#

  
 
#--------------------------------------------------------------------------------
#
# Copy Endoscopy
#
  def setCameraNode(self, newCameraNode):
    """Allow to set the current camera node.
    Connected to signal 'currentNodeChanged()' emitted by camera node selector."""

    #  Remove previous observer
    if self.cameraNode and self.cameraNodeObserverTag:
      self.cameraNode.RemoveObserver(self.cameraNodeObserverTag)
    if self.camera and self.cameraObserverTag:
      self.camera.RemoveObserver(self.cameraObserverTag)

    newCamera = None
    if newCameraNode:
      newCamera = newCameraNode.GetCamera()
      # Add CameraNode ModifiedEvent observer
      self.cameraNodeObserverTag = newCameraNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onCameraNodeModified)
      # Add Camera ModifiedEvent observer
      self.cameraObserverTag = newCamera.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onCameraNodeModified)

    self.cameraNode = newCameraNode
    self.camera = newCamera

    # Update UI
    self.updateWidgetFromMRML()

  def updateWidgetFromMRML(self):
    if self.camera:
      self.viewAngleSlider.value = self.camera.GetViewAngle()
    if self.cameraNode:
      pass

  def onCameraModified(self, observer, eventid):
    self.updateWidgetFromMRML()

  def onCameraNodeModified(self, observer, eventid):
    self.updateWidgetFromMRML()


  def enableOrDisableCreateButton(self):
    """Connected to both the fiducial and camera node selector. It allows to
    enable or disable the 'create path' button."""
    self.createPathButton.enabled = self.cameraNodeSelector.currentNode() is not None and self.inputFiducialsNodeSelector.currentNode() is not None

  def onCreatePathButtonClicked(self):
    """Connected to 'create path' button. It allows to:
      - compute the path
      - create the associated model"""

    fiducialsNode = self.inputFiducialsNodeSelector.currentNode();
    print "Calculating Path..."
    result = EndoscopyComputePath(fiducialsNode)
    print "-> Computed path contains %d elements" % len(result.path)

    print "Create Model..."
    model = EndoscopyPathModel(result.path, fiducialsNode)
    print "-> Model created"

    # Update frame slider range
    self.frameSlider.maximum = len(result.path) - 2

    # Update flythrough variables
    self.camera = self.camera
    self.transform = model.transform
    self.pathPlaneNormal = model.planeNormal
    self.path = result.path

    # Enable / Disable flythrough button
    self.flythroughCollapsibleButton.enabled = len(result.path) > 0

  def frameSliderValueChanged(self, newValue):
    #print "frameSliderValueChanged:", newValue
    self.flyTo(newValue)

  def frameSkipSliderValueChanged(self, newValue):
    #print "frameSkipSliderValueChanged:", newValue
    self.skip = int(newValue)

  def frameDelaySliderValueChanged(self, newValue):
    #print "frameDelaySliderValueChanged:", newValue
    self.timer.interval = newValue

  def viewAngleSliderValueChanged(self, newValue):
    if not self.cameraNode:
      return
    #print "viewAngleSliderValueChanged:", newValue
    self.cameraNode.GetCamera().SetViewAngle(newValue)

  def onPlayButtonToggled(self, checked):
    if checked:
      self.timer.start()
      self.playButton.text = "Stop"
    else:
      self.timer.stop()
      self.playButton.text = "Play"

  def flyToNext(self):
    currentStep = self.frameSlider.value
    nextStep = currentStep + self.skip + 1
    if nextStep > len(self.path) - 2:
      nextStep = 0
    self.frameSlider.value = nextStep

  def flyTo(self, f):
    """ Apply the fth step in the path to the global camera"""
    if self.path:
      f = int(f)
      p = self.path[f]
      self.camera.SetPosition(*p)
      foc = self.path[f+1]
      self.camera.SetFocalPoint(*foc)

      toParent = vtk.vtkMatrix4x4()
      self.transform.GetMatrixTransformToParent(toParent)
      toParent.SetElement(0 ,3, p[0])
      toParent.SetElement(1, 3, p[1])
      toParent.SetElement(2, 3, p[2])

      # Set up transform orientation component so that
      # Z axis is aligned with view direction and
      # Y vector is aligned with the curve's plane normal.
      # This can be used for example to show a reformatted slice
      # using with SlicerIGT extension's VolumeResliceDriver module.
      import numpy as np
      zVec = (foc-p)/np.linalg.norm(foc-p)
      yVec = self.pathPlaneNormal
      xVec = np.cross(yVec, zVec)
      toParent.SetElement(0, 0, xVec[0])
      toParent.SetElement(1, 0, xVec[1])
      toParent.SetElement(2, 0, xVec[2])
      toParent.SetElement(0, 1, yVec[0])
      toParent.SetElement(1, 1, yVec[1])
      toParent.SetElement(2, 1, yVec[2])
      toParent.SetElement(0, 2, zVec[0])
      toParent.SetElement(1, 2, zVec[1])
      toParent.SetElement(2, 2, zVec[2])

      self.transform.SetMatrixTransformToParent(toParent)
  
#
# Copy Endoscopy
#
#================================================================================



class CoronaryArteryAnalysisLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

  def run(self, inputVolume, outputVolume, imageThreshold, enableScreenshots=0):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

    # Capture screenshot
    if enableScreenshots:
      self.takeScreenshot('CoronaryArteryAnalysisTest-Start','MyScreenshot',-1)

    logging.info('Processing completed')

    return True


class CoronaryArteryAnalysisTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_CoronaryArteryAnalysis1()

  def test_CoronaryArteryAnalysis1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = CoronaryArteryAnalysisLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')




  
#--------------------------------------------------------------------------------
#
# Copy Endoscopy
#
class EndoscopyComputePath:
  """Compute path given a list of fiducials.
  A Hermite spline interpolation is used. See http://en.wikipedia.org/wiki/Cubic_Hermite_spline

  Example:
    result = EndoscopyComputePath(fiducialListNode)
    print "computer path has %d elements" % len(result.path)

  """

  def __init__(self, fiducialListNode, dl = 0.5):
    import numpy
    self.dl = dl # desired world space step size (in mm)
    self.dt = dl # current guess of parametric stepsize
    self.fids = fiducialListNode

    # hermite interpolation functions
    self.h00 = lambda t: 2*t**3 - 3*t**2     + 1
    self.h10 = lambda t:   t**3 - 2*t**2 + t
    self.h01 = lambda t:-2*t**3 + 3*t**2
    self.h11 = lambda t:   t**3 -   t**2

    # n is the number of control points in the piecewise curve

    if self.fids.GetClassName() == "vtkMRMLAnnotationHierarchyNode":
      # slicer4 style hierarchy nodes
      collection = vtk.vtkCollection()
      self.fids.GetChildrenDisplayableNodes(collection)
      self.n = collection.GetNumberOfItems()
      if self.n == 0:
        return
      self.p = numpy.zeros((self.n,3))
      for i in xrange(self.n):
        f = collection.GetItemAsObject(i)
        coords = [0,0,0]
        f.GetFiducialCoordinates(coords)
        self.p[i] = coords
    elif self.fids.GetClassName() == "vtkMRMLMarkupsFiducialNode":
      # slicer4 Markups node
      self.n = self.fids.GetNumberOfFiducials()
      n = self.n
      if n == 0:
        return
      # get fiducial positions
      # sets self.p
      self.p = numpy.zeros((n,3))
      for i in xrange(n):
        coord = [0.0, 0.0, 0.0]
        self.fids.GetNthFiducialPosition(i, coord)
        self.p[i] = coord
    else:
      # slicer3 style fiducial lists
      self.n = self.fids.GetNumberOfFiducials()
      n = self.n
      if n == 0:
        return
      # get control point data
      # sets self.p
      self.p = numpy.zeros((n,3))
      for i in xrange(n):
        self.p[i] = self.fids.GetNthFiducialXYZ(i)

    # calculate the tangent vectors
    # - fm is forward difference
    # - m is average of in and out vectors
    # - first tangent is out vector, last is in vector
    # - sets self.m
    n = self.n
    fm = numpy.zeros((n,3))
    for i in xrange(0,n-1):
      fm[i] = self.p[i+1] - self.p[i]
    self.m = numpy.zeros((n,3))
    for i in xrange(1,n-1):
      self.m[i] = (fm[i-1] + fm[i]) / 2.
    self.m[0] = fm[0]
    self.m[n-1] = fm[n-2]

    self.path = [self.p[0]]
    self.calculatePath()

  def calculatePath(self):
    """ Generate a flight path for of steps of length dl """
    #
    # calculate the actual path
    # - take steps of self.dl in world space
    # -- if dl steps into next segment, take a step of size "remainder" in the new segment
    # - put resulting points into self.path
    #
    n = self.n
    segment = 0 # which first point of current segment
    t = 0 # parametric current parametric increment
    remainder = 0 # how much of dl isn't included in current step
    while segment < n-1:
      t, p, remainder = self.step(segment, t, self.dl)
      if remainder != 0 or t == 1.:
        segment += 1
        t = 0
        if segment < n-1:
          t, p, remainder = self.step(segment, t, remainder)
      self.path.append(p)

  def point(self,segment,t):
    return (self.h00(t)*self.p[segment] +
              self.h10(t)*self.m[segment] +
              self.h01(t)*self.p[segment+1] +
              self.h11(t)*self.m[segment+1])

  def step(self,segment,t,dl):
    """ Take a step of dl and return the path point and new t
      return:
      t = new parametric coordinate after step
      p = point after step
      remainder = if step results in parametic coordinate > 1.0, then
        this is the amount of world space not covered by step
    """
    import numpy.linalg
    p0 = self.path[self.path.__len__() - 1] # last element in path
    remainder = 0
    ratio = 100
    count = 0
    while abs(1. - ratio) > 0.05:
      t1 = t + self.dt
      pguess = self.point(segment,t1)
      dist = numpy.linalg.norm(pguess - p0)
      ratio = self.dl / dist
      self.dt *= ratio
      if self.dt < 0.00000001:
        return
      count += 1
      if count > 500:
        return (t1, pguess, 0)
    if t1 > 1.:
      t1 = 1.
      p1 = self.point(segment, t1)
      remainder = numpy.linalg.norm(p1 - pguess)
      pguess = p1
    return (t1, pguess, remainder)


class EndoscopyPathModel:
  """Create a vtkPolyData for a polyline:
       - Add one point per path point.
       - Add a single polyline
  """
  def __init__(self, path, fiducialListNode):

    fids = fiducialListNode
    scene = slicer.mrmlScene

    points = vtk.vtkPoints()
    polyData = vtk.vtkPolyData()
    polyData.SetPoints(points)

    lines = vtk.vtkCellArray()
    polyData.SetLines(lines)
    linesIDArray = lines.GetData()
    linesIDArray.Reset()
    linesIDArray.InsertNextTuple1(0)

    polygons = vtk.vtkCellArray()
    polyData.SetPolys( polygons )
    idArray = polygons.GetData()
    idArray.Reset()
    idArray.InsertNextTuple1(0)

    for point in path:
      pointIndex = points.InsertNextPoint(*point)
      linesIDArray.InsertNextTuple1(pointIndex)
      linesIDArray.SetTuple1( 0, linesIDArray.GetNumberOfTuples() - 1 )
      lines.SetNumberOfCells(1)

    import vtk.util.numpy_support as VN
    pointsArray = VN.vtk_to_numpy(points.GetData())
    self.planePosition, self.planeNormal = self.planeFit(pointsArray.T)

    # Create model node
    model = slicer.vtkMRMLModelNode()
    model.SetScene(scene)
    model.SetName(scene.GenerateUniqueName("Path-%s" % fids.GetName()))
    model.SetAndObservePolyData(polyData)

    # Create display node
    modelDisplay = slicer.vtkMRMLModelDisplayNode()
    modelDisplay.SetColor(1,1,0) # yellow
    modelDisplay.SetScene(scene)
    scene.AddNode(modelDisplay)
    model.SetAndObserveDisplayNodeID(modelDisplay.GetID())

    # Add to scene
    scene.AddNode(model)

    # Camera cursor
    sphere = vtk.vtkSphereSource()
    sphere.Update()

    # Create model node
    cursor = slicer.vtkMRMLModelNode()
    cursor.SetScene(scene)
    cursor.SetName(scene.GenerateUniqueName("Cursor-%s" % fids.GetName()))
    cursor.SetPolyDataConnection(sphere.GetOutputPort())

    # Create display node
    cursorModelDisplay = slicer.vtkMRMLModelDisplayNode()
    cursorModelDisplay.SetColor(1,0,0) # red
    cursorModelDisplay.SetScene(scene)
    scene.AddNode(cursorModelDisplay)
    cursor.SetAndObserveDisplayNodeID(cursorModelDisplay.GetID())

    # Add to scene
    scene.AddNode(cursor)

    # Create transform node
    transform = slicer.vtkMRMLLinearTransformNode()
    transform.SetName(scene.GenerateUniqueName("Transform-%s" % fids.GetName()))
    scene.AddNode(transform)
    cursor.SetAndObserveTransformNodeID(transform.GetID())

    self.transform = transform

  # source: http://stackoverflow.com/questions/12299540/plane-fitting-to-4-or-more-xyz-points
  def planeFit(self, points):
    """
    p, n = planeFit(points)

    Given an array, points, of shape (d,...)
    representing points in d-dimensional space,
    fit an d-dimensional plane to the points.
    Return a point, p, on the plane (the point-cloud centroid),
    and the normal, n.
    """
    import numpy as np
    from numpy.linalg import svd
    points = np.reshape(points, (np.shape(points)[0], -1)) # Collapse trialing dimensions
    assert points.shape[0] <= points.shape[1], "There are only {} points in {} dimensions.".format(points.shape[1], points.shape[0])
    ctr = points.mean(axis=1)
    x = points - ctr[:,np.newaxis]
    M = np.dot(x, x.T) # Could also use np.cov(x) here.
    return ctr, svd(M)[0][:,-1]


#
# Copy Endoscopy
#
#================================================================================
