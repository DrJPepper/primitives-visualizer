import sys
import json
import argparse
from pathlib import Path
from copy import deepcopy

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton
from PyQt5.QtCore import QFile, QIODevice
from PyQt5.uic import loadUi
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk

TUBE_RADIUS_DEFAULT = 0.05
SPHERE_RADIUS_DEFAULT = 0.1

# Subclass QMainWindow similarly to in C++
class MainWindow(QMainWindow):

    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)

        parser = argparse.ArgumentParser(
                prog = 'PrimitivesVisualizer',
                description = 'Visualizes 3D geometry from a JSON file',
                epilog = 'Filename can also be specified in ./default_input.txt'
                )
        parser.add_argument('-b', '--basic-mode', required=False,
                            action=argparse.BooleanOptionalAction)
        parser.add_argument('-n', '--no-reset', required=False,
                            action=argparse.BooleanOptionalAction)
        parser.add_argument('-f', '--filename', required=False)
        parser.add_argument('-t', '--tube-radius', required=False, type=float)
        parser.add_argument('-s', '--sphere-radius', required=False, type=float)
        args = parser.parse_args()
        if args.filename is None:
            default_file = Path("./default_input.txt")
            if default_file.is_file():
                filename = open("./default_input.txt").readline().strip()
            else:
                print("Error: no input file name supplied")
                parser.print_help()
                exit(1)
        else:
            filename = args.filename
        tube_radius = TUBE_RADIUS_DEFAULT
        sphere_radius = SPHERE_RADIUS_DEFAULT
        if args.tube_radius is not None:
            tube_radius = args.tube_radius
        if args.sphere_radius is not None:
            sphere_radius = args.sphere_radius

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


        reset_camera()
        self.show()
        # Associate needed objects with the callback function object itself
        callback_function.ren = self.ren
        callback_function.info_box = self.infoBox
        callback_function.basic = args.basic_mode
        # Set up callback
        self.iren.AddObserver('LeftButtonPressEvent', callback_function)
        if args.basic_mode:
            load_basic_scene.ren = self.ren
            load_basic_scene.filename = filename
            load_basic_scene.tube_radius = tube_radius
            load_basic_scene.sphere_radius = sphere_radius
            load_basic_scene.done = False
            load_basic_scene()
        else:
            self.runallButton.clicked.connect(run_all)
            self.continueButton.clicked.connect(load_next)
            json_doc = json.load(open(filename))
            # Associate a lot of persistent information with load_next
            load_next.reset = not args.no_reset
            load_next.i = 0
            load_next.ren = self.ren
            load_next.json_doc = json_doc
            load_next.actors = []
            load_next.hold_actors = []
            load_next.positions = [[], [], []]
            load_next.hold_positions = [[], [], []]
            load_next.cube_axis = None
            load_next.descriptions = {}
            load_next.tube_radius = tube_radius
            load_next.sphere_radius = sphere_radius
            load_next()

def export_scene():
    export_scene.exporter.Update()

def reset_camera():
    reset_camera.ren.ResetCamera()
    reset_camera.renWin.Render()

"""
Prints information on the selected entity to an info box in the GUI
"""
def callback_function(caller, ev):
    picker = vtk.vtkPropPicker()
    pos = caller.GetEventPosition()
    picker.PickProp(pos[0], pos[1], callback_function.ren)
    picked_actor = picker.GetActor()
    if picked_actor:
        pos = picker.GetPickPosition()
        string = f'3D Scene Position: {pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}\n\n'
        if not callback_function.basic:
            string += str(load_next.descriptions[picked_actor])
        callback_function.info_box.setPlainText(string)
    else:
        callback_function.info_box.setPlainText(
                f'2D Window Position: {pos[0]:.2f}, {pos[1]:.2f}\n\n' +
                'No actor picked')

"""
Runs through all entities in the list (not an instantaneous process)
"""
def run_all():
    while load_next.i < len(load_next.json_doc['list']):
        load_next()

"""
Loads basic mode scene
"""
def load_basic_scene():
    if load_basic_scene.done:
        print("No more scenes to render")
        return
    try:
        scene = [[float(j) for j in i.strip().split(',')] for i in
               open(load_basic_scene.filename).readlines() if i != '\n' and
                 '#' not in i]
    except ValueError:
        scene = [[float(j) for j in i.strip().split()] for i in
               open(load_basic_scene.filename).readlines() if i != '\n' and
                 '#' not in i]
    positions = [[], [], []]
    for entity in scene:
        if len(entity) == 6:
            for i in range(3):
                positions[i].append(entity[i+3])
        for i in range(3):
            positions[i].append(entity[i])
        actor = None
        if len(entity) == 3:
            source = vtk.vtkSphereSource()
            source.SetRadius(load_basic_scene.sphere_radius)
            source.SetCenter(entity)
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(source.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            #actor.GetProperty().SetColor(entity['color'])
            #actor.GetProperty().SetOpacity(entity['opacity'])
        elif len(entity) == 6:
            line_source = vtk.vtkLineSource()
            line_source.SetPoint1(entity[:3])
            line_source.SetPoint2(entity[3:])
            line_source.SetResolution(6)
            line_source.Update()
            tube_filter = vtk.vtkTubeFilter()
            tube_filter.SetInputConnection(line_source.GetOutputPort())
            tube_filter.SetNumberOfSides(8)
            tube_filter.SetRadius(load_basic_scene.tube_radius)
            tube_filter.Update()
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(tube_filter.GetOutputPort())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            #actor.GetProperty().SetColor(entity['color'])
            #actor.GetProperty().SetOpacity(entity['opacity'])
        load_basic_scene.ren.AddActor(actor)

    # Make the axes actor to the correct sizing based on the elements on screen
    cube_axis = vtk.vtkCubeAxesActor()
    cube_axis.SetCamera(load_basic_scene.ren.GetActiveCamera());
    mins = [min(i) for i in positions]
    maxs = [max(i) for i in positions]
    dists = [i[0] - i[1] for i in zip(maxs, mins)]
    mins = [i[0] - max(load_basic_scene.sphere_radius, i[1] * 0.1) for i in zip(mins, dists)]
    maxs = [i[0] + max(load_basic_scene.sphere_radius, i[1] * 0.1) for i in zip(maxs, dists)]
    cube_axis.SetFlyModeToStaticEdges()
    cube_axis.SetBounds((mins[0], maxs[0], mins[1], maxs[1],
        mins[2], maxs[2]))
    load_basic_scene.ren.AddActor(cube_axis)

    reset_camera()

"""
Loads the next entity into the scene, and clears it if appropriate
"""
def load_next():
    if load_next.i > len(load_next.json_doc['list']) - 1:
        print("No more scenes to render")
        return

    curr = load_next.json_doc['list'][load_next.i]
    # List of entities to process
    scene = curr['entities']
    # Whether this scene should be persistent through resets
    hold = 'hold' in curr.keys() and curr['hold']
    if 'reset' in curr:
        curr_reset_check = curr['reset']
    else:
        curr_reset_check = False
    # Perform a reset if requested
    if ('reset' not in load_next.json_doc.keys() or\
            load_next.json_doc['reset']) or\
            curr_reset_check:
        load_next.positions = deepcopy(load_next.hold_positions)
        for actor in load_next.actors:
            # Hold the actors marked as such
            if actor not in load_next.hold_actors:
                load_next.ren.RemoveActor(actor)
        load_next.actors = []
    # Process every entity within this scene/JSON entry
    for entity in scene:
        # Determine how large to make the axes
        for i in range(len(entity['position'])):
            load_next.positions[i % 3].append(entity['position'][i])
            if hold:
                load_next.hold_positions[i % 3].append(entity['position'][i])
        actor = None
        if entity['type'] == 'point':
            source = vtk.vtkSphereSource()
            source.SetRadius(load_next.sphere_radius)
            source.SetCenter(entity['position'])
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(source.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(entity['color'])
            actor.GetProperty().SetOpacity(entity['opacity'])
        elif entity['type'] == 'vector':
            line_source = vtk.vtkLineSource()
            line_source.SetPoint1(entity['position'][:3])
            line_source.SetPoint2(entity['position'][3:])
            line_source.SetResolution(6)
            line_source.Update()
            tube_filter = vtk.vtkTubeFilter()
            tube_filter.SetInputConnection(line_source.GetOutputPort())
            tube_filter.SetNumberOfSides(8)
            tube_filter.SetRadius(load_next.tube_radius)
            tube_filter.Update()
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(tube_filter.GetOutputPort())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(entity['color'])
            actor.GetProperty().SetOpacity(entity['opacity'])
        load_next.ren.AddActor(actor)
        load_next.actors.append(actor)
        if hold:
            load_next.hold_actors.append(actor)
        if actor:
            load_next.descriptions[actor] = entity['description']

    # Make the axes actor to the correct sizing based on the elements on screen
    cube_axis = vtk.vtkCubeAxesActor()
    cube_axis.SetCamera(load_next.ren.GetActiveCamera());
    mins = [min(i) for i in load_next.positions]
    maxs = [max(i) for i in load_next.positions]
    dists = [i[0] - i[1] for i in zip(maxs, mins)]
    mins = [i[0] - max(load_next.sphere_radius, i[1] * 0.1) for i in zip(mins, dists)]
    maxs = [i[0] + max(load_next.sphere_radius, i[1] * 0.1) for i in zip(maxs, dists)]
    cube_axis.SetFlyModeToStaticEdges()
    cube_axis.SetBounds((mins[0], maxs[0], mins[1], maxs[1],
        mins[2], maxs[2]))
    load_next.ren.AddActor(cube_axis)
    if load_next.cube_axis:
        load_next.ren.RemoveActor(load_next.cube_axis)
    load_next.cube_axis = cube_axis

    load_next.i += 1

    if (load_next.i == 1 or load_next.reset):
        reset_camera()
    reset_camera.renWin.Render()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
