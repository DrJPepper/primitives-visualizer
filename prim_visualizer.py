import sys
import json

import numpy as np

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton
from PyQt5.QtCore import QFile, QIODevice
from PyQt5.uic import loadUi
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk

TUBE_RADIUS = 0.05
SPHERE_RADIUS = 0.1

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

        #json_doc = json.load(open('../4d_multilayer_modeler/build/out.json'))
        json_doc = json.load(open('../tissue_sim/build/out.json'))
        print(json_doc)
        self.continueButton.clicked.connect(load_next)
        load_next.i = 0
        load_next.ren = self.ren
        load_next.json_doc = json_doc
        load_next.actors = []
        load_next.positions = [[], [], []]
        load_next.cube_axis = None
        load_next.descriptions = {}
        reset_camera()
        self.show()
        load_next()
        #self.iren.Initialize()

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
    if picked_actor:
        pos = picker.GetPickPosition()
        callback_function.info_box.setPlainText(
                f'3D Scene Position: {pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}\n\n' +
                load_next.descriptions[picked_actor])
    else:
        callback_function.info_box.setPlainText(
                f'2D Window Position: {pos[0]:.2f}, {pos[1]:.2f}\n\n' +
                'No actor picked')

def load_next():
    if (load_next.i > len(load_next.json_doc['list']) - 1):
        print("No more scenes to render")
        return

    scene = load_next.json_doc['list'][load_next.i]['entities']
    if 'reset' in load_next.json_doc['list'][load_next.i]:
        curr_reset_check = load_next.json_doc['list'][load_next.i]['reset']
    else:
        curr_reset_check = False
    #print(load_next.actors)
    if ('reset' not in load_next.json_doc.keys() or\
            load_next.json_doc['reset']) or\
            curr_reset_check:
        load_next.positions = [[], [], []]
        for actor in load_next.actors:
            load_next.ren.RemoveActor(actor)
        load_next.actors = []
    for entity in scene:
        for i in range(len(entity['position'])):
            load_next.positions[i % 3].append(entity['position'][i])
        actor = None
        if entity['type'] == 'point':
            source = vtk.vtkSphereSource()
            source.SetRadius(SPHERE_RADIUS)
            source.SetCenter(entity['position'])
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(source.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(entity['color'])
            load_next.ren.AddActor(actor)
            load_next.actors.append(actor)
        elif entity['type'] == 'vector':
            line_source = vtk.vtkLineSource()
            line_source.SetPoint1(entity['position'][:3])
            line_source.SetPoint2(entity['position'][3:])
            line_source.SetResolution(6)
            line_source.Update()
            tube_filter = vtk.vtkTubeFilter()
            tube_filter.SetInputConnection(line_source.GetOutputPort())
            tube_filter.SetNumberOfSides(8)
            tube_filter.SetRadius(TUBE_RADIUS)
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
            load_next.ren.AddActor(actor)
            load_next.actors.append(actor)
            #glyph.SetVectorModeToUseNormal();
            #glyph.SetScaleModeToScaleByVector();
            #glyph.SetScaleFactor(size);
            #glyph.OrientOn();
            #glyph.Update();
        if actor:
            load_next.descriptions[actor] = entity['description']

    cube_axis = vtk.vtkCubeAxesActor()
    cube_axis.SetCamera(load_next.ren.GetActiveCamera());
    mins = [min(i) for i in load_next.positions]
    maxs = [max(i) for i in load_next.positions]
    dists = [i[0] - i[1] for i in zip(maxs, mins)]
    mins = [i[0] - max(SPHERE_RADIUS, i[1] * 0.1) for i in zip(mins, dists)]
    maxs = [i[0] + max(SPHERE_RADIUS, i[1] * 0.1) for i in zip(maxs, dists)]
    cube_axis.SetFlyModeToStaticEdges()
    cube_axis.SetBounds((mins[0], maxs[0], mins[1], maxs[1],
        mins[2], maxs[2]))
    load_next.ren.AddActor(cube_axis)
    if load_next.cube_axis:
        load_next.ren.RemoveActor(load_next.cube_axis)
    load_next.cube_axis = cube_axis

    load_next.i += 1

    reset_camera()
    #self.show()
    #self.iren.Initialize()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
