import sys
import json

import numpy as np

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton
from PyQt5.QtCore import QFile, QIODevice
from PyQt5.uic import loadUi
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk

# Subclass QMainWindow similarly to in C++
class MainWindow(QMainWindow):

    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)

        # Load the .ui file and associate its content with this MainWindow
        loadUi("window.ui", self)

        # Add the render window to the frame from the .ui file,
        # then make it fill the whole frame
        self.vtkWidget = QVTKRenderWindowInteractor(self.qvtkFrame)
        self.vtkWidget.setFixedSize(self.qvtkFrame.size())

        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

        self.exporter = vtk.vtkOBJExporter()
        self.exporter.SetActiveRenderer(self.ren)
        self.exporter.SetRenderWindow(self.vtkWidget.GetRenderWindow())
        self.exporter.SetFilePrefix("prim-vis")

        colors = vtk.vtkNamedColors()

        # Buttons
        reset_camera.ren = self.ren
        reset_camera.renWin = self.vtkWidget.GetRenderWindow()
        self.centerButton.clicked.connect(reset_camera)

        export_scene.exporter = self.exporter
        self.exportButton.clicked.connect(export_scene)

        # Associate needed objects with the callback function object itself
        callback_function.ren = self.ren
        callback_function.info_box = self.infoBox
        # Set up callback
        self.iren.AddObserver('LeftButtonPressEvent', callback_function)

        scene = json.load(open('../4d_multilayer_modeler/build/out.json'))\
                ['list'][0]['entities']
        positions = [[], [], []]
        for entity in scene:
            for i in range(len(entity['position'])):
                positions[i % 3].append(entity['position'][i])
            if entity['type'] == 'point':
                source = vtk.vtkSphereSource()
                source.SetRadius(0.1)
                source.SetCenter(entity['position'])
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(source.GetOutputPort())

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(entity['color'])
                self.ren.AddActor(actor)
            elif entity['type'] == 'vector':
                line_source = vtk.vtkLineSource()
                line_source.SetPoint1(entity['position'][:3])
                line_source.SetPoint2(entity['position'][3:])
                line_source.SetResolution(6)
                line_source.Update()
                tube_filter = vtk.vtkTubeFilter()
                tube_filter.SetInputConnection(line_source.GetOutputPort())
                tube_filter.SetNumberOfSides(8)
                tube_filter.SetRadius(0.05)
                tube_filter.Update()
                #arrow = vtk.vtkArrowSource()
                #arrow.SetTipResolution(16)
                #arrow.SetTipLength(0.3)
                #arrow.SetTipRadius(0.1)
                #glyph = vtk.vtkGlyph3D()
                #glyph.SetSourceConnection(arrow.GetOutputPort())
                #glyph.SetInputData(tube_filter.GetOutput())
                mapper = vtk.vtkPolyDataMapper()
                #mapper.SetInputConnection(glyph.GetOutputPort())
                mapper.SetInputConnection(tube_filter.GetOutputPort())
                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(entity['color'])
                self.ren.AddActor(actor)
                #glyph.SetVectorModeToUseNormal();
                #glyph.SetScaleModeToScaleByVector();
                #glyph.SetScaleFactor(size);
                #glyph.OrientOn();
                #glyph.Update();

        cube_axis = vtk.vtkCubeAxesActor()
        cube_axis.SetCamera(self.ren.GetActiveCamera());
        mins = [min(i) for i in positions]
        maxs = [max(i) for i in positions]
        cube_axis.SetFlyModeToStaticEdges()
        cube_axis.SetBounds((mins[0], maxs[0], mins[1], maxs[1],
            mins[2], maxs[2]))
        self.ren.AddActor(cube_axis)

        reset_camera()
        self.show()
        self.iren.Initialize()

def export_scene():
    export_scene.exporter.Update()

def reset_camera():
    reset_camera.ren.ResetCamera()
    reset_camera.renWin.Render()

def callback_function(caller, ev):
    picker = vtk.vtkPropPicker()
    pos = caller.GetEventPosition()
    picker.PickProp(pos[0], pos[1], callback_function.ren)
    picked_actor = picker.GetActor()
    pos = picker.GetPickPosition()
    callback_function.info_box.setPlainText(f'{pos[0]}, {pos[1]}, {pos[2]}')

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
