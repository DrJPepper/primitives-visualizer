import sys
import calendar
import time
import os
import json
import argparse
from pathlib import Path
from copy import deepcopy

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton,\
                            QSizePolicy
from PyQt5.QtCore import QFile, QIODevice
from PyQt5.uic import loadUi
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
import numpy as np

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
        parser.add_argument('-l', '--light-mode', required=False,
                            action=argparse.BooleanOptionalAction)
        parser.add_argument('-m', '--model-mode', required=False,
                            action=argparse.BooleanOptionalAction)
        parser.add_argument('-o', '--obj-mode', required=False,
                            action=argparse.BooleanOptionalAction)
        parser.add_argument('-b', '--basic-mode', required=False,
                            action=argparse.BooleanOptionalAction)
        parser.add_argument('-r', '--render-mode', required=False,
                            action=argparse.BooleanOptionalAction)
        parser.add_argument('-c', '--scalar-field-mode', required=False,
                            action=argparse.BooleanOptionalAction)
        parser.add_argument('-n', '--no-reset', required=False,
                            action=argparse.BooleanOptionalAction)
        parser.add_argument('-f', '--filename', required=False)
        parser.add_argument('-t', '--tube-radius', required=False, type=float)
        parser.add_argument('-s', '--sphere-radius', required=False,
                            type=float)
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
        pyfile_path = os.path.dirname(os.path.realpath(__file__))
        loadUi(os.path.join(pyfile_path, 'window.ui'), self)

        # Add the render window to the frame from the .ui file,
        # then make it fill the whole frame
        self.vtkWidget = QVTKRenderWindowInteractor()
        self.horizontalLayout_2.addWidget(self.vtkWidget)
        self.vtkWidget.setSizePolicy(QSizePolicy.Expanding,
                QSizePolicy.Expanding)

        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

        self.exporter = vtk.vtkOBJExporter()
        self.exporter.SetActiveRenderer(self.ren)
        self.exporter.SetRenderWindow(self.vtkWidget.GetRenderWindow())
        self.exporter.SetFilePrefix("prim-vis")

        colors = vtk.vtkNamedColors()

        if args.light_mode:
            self.ren.SetBackground(colors.GetColor3d("white"));

        # Buttons
        reset_camera.ren = self.ren
        reset_camera.renWin = self.vtkWidget.GetRenderWindow()
        self.centerButton.clicked.connect(reset_camera)

        export_scene.exporter = self.exporter
        self.exportButton.clicked.connect(export_scene)

        export_png.renWin = self.vtkWidget.GetRenderWindow()
        self.pngButton.clicked.connect(export_png)

        reset_camera()
        self.show()
        # Associate needed objects with the callback function object itself
        callback_function.ren = self.ren
        callback_function.info_box = self.infoBox
        callback_function.basic = args.basic_mode
        json_doc = None
        # Set up callback
        if not (args.basic_mode or args.model_mode or args.obj_mode):
            if args.render_mode:
                batch_json = json.load(open(filename))
                json_doc = {}
                json_doc["list"] = []
                json_doc["glyph"] = True
                sr = batch_json["scale_factor"] * 0.05
                tr = batch_json["scale_factor"] * 0.025
                for step in batch_json["positions"]:
                    entry = {}
                    entry["entities"] = []
                    bpts = step["positions"]
                    points = []
                    for i in range(0, len(bpts), 3):
                        points.append([bpts[i], bpts[i+1], bpts[i+2]])
                        entry["entities"].append(
                                {"type": "point",
                                 "position": points[-1],
                                 "color": [1.0, 1.0, 1.0],
                                 "radius": sr})
                    for edge in batch_json["edges"]:
                        l = dist(points[edge["vertices"][0]], points[edge["vertices"][1]])
                        c = ratio_to_rgb(l / edge["rest_length"])
                        entry["entities"].append(
                                {"type": "vector",
                                 "position": points[edge["vertices"][0]] +
                                 points[edge["vertices"][1]],
                                 "color": c,
                                 "radius": tr})
                    json_doc["list"].append(entry)
                    break
            else:
                json_doc = json.load(open(filename))
            if "glyph" not in json_doc.keys() or not json_doc["glyph"]:
                self.iren.AddObserver(
                        'LeftButtonPressEvent', callback_function)
        elif args.model_mode:
            self.iren.AddObserver('LeftButtonPressEvent', model_callback)
        if args.basic_mode:
            load_basic_scene.ren = self.ren
            load_basic_scene.filename = filename
            load_basic_scene.tube_radius = tube_radius
            load_basic_scene.sphere_radius = sphere_radius
            load_basic_scene.done = False
            load_basic_scene()
        elif args.scalar_field_mode:
            load_scalar_field.ren = self.ren
            load_scalar_field.json_doc = json_doc
            load_scalar_field()
        elif args.obj_mode:
            load_obj.ren = self.ren
            load_obj.light_mode = args.light_mode
            load_obj.filename = filename
            load_obj.ren_win = self.vtkWidget.GetRenderWindow()
            load_obj()
        elif args.model_mode:
            load_model.ren = self.ren
            load_model.descriptions = {}
            load_model.tube_radius = tube_radius
            load_model.sphere_radius = sphere_radius
            load_model.filename = filename
            load_model.ren_win = self.vtkWidget.GetRenderWindow()
            load_model.done = False
            load_model.info_box = self.infoBox
            load_model()
        else:
            self.runallButton.clicked.connect(run_all)
            self.continueButton.clicked.connect(load_next)
            #json_doc = json.load(open(filename))
            #print(json_doc.keys())
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
            load_next.vtkWidget = self.vtkWidget
            load_next()

def load_scalar_field():
    jd = load_scalar_field.json_doc
    #print(jd['edges'][jd['cells'][0]['edges'][0]])
    vertices = []
    faces = []
    colors = []
    colorDict = {}
    for v in jd['vertices']:
        v['new_index'] = -1
    #for e in jd['edges']:
    #    e['center_index'] = -1
    #    e['center'] = [-1, -1, -1]
    #    if not e['type']:
    #        e['center'] = [i[0]+i[1]/2.0 for i in [jd['vertices'][j]['position'] for j in e['vertices']]] + [0.0]
    #        vertices.append(e['center'])
    #        e['center_index'] = len(vertices) - 1
    for c in jd['cells']:
        center = np.array([0.0, 0.0, 0.0])
        count = 0
        for e in c['edges']:
            edge = jd['edges'][e]
            if not edge['type']:
                for v in edge['vertices']:
                    vertex = jd['vertices'][v]
                    center += np.array(vertex['position'])
                    count += 1
                    if vertex['new_index'] == -1:
                        vertices.append(vertex['position'])
                        vertex['new_index'] = len(vertices) - 1
        center /= count
        c['center'] = center.tolist()
        vertices.append(c['center'])
        c['center_index'] = len(vertices) - 1
        for e in c['edges']:
            edge = jd['edges'][e]
            if not edge['type']:
                v1 = jd['vertices'][edge['vertices'][0]]['new_index']
                v2 = jd['vertices'][edge['vertices'][1]]['new_index']
                #ec = edge['center_index']
                cc = c['center_index']
                #faces.append([v1, ec, cc])
                #faces.append([ec, v2, cc])
                faces.append([v1, v2, cc])

                #print(f'{v1}, {v2}, {ec}, {cc}')

    points = vtk.vtkPoints()
    triangles = vtk.vtkCellArray()
    for i in vertices:
        points.InsertNextPoint(i)
    for i in faces:
        triangle = vtk.vtkTriangle()
        triangle.GetPointIds().SetId(0, i[0]);
        triangle.GetPointIds().SetId(1, i[1]);
        triangle.GetPointIds().SetId(2, i[2]);
        triangles.InsertNextCell(triangle)

    polyData = vtk.vtkPolyData()
    polyData.SetPoints(points)
    polyData.SetPolys(triangles)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polyData)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    #actor->GetProperty()->SetColor(
    #        colors->GetColor3d(theme.tris).GetData());
    load_scalar_field.ren.AddActor(actor);
    #load_scalar_field.ren.ResetCamera();
    reset_camera()

def dist(p1, p2):
    np1 = np.array(p1)
    np2 = np.array(p2)
    return np.linalg.norm(np1 - np2)

def ratio_to_rgb(ratio):
    cap = 0.05
    min_cap = 1.0 - cap
    max_cap = 1.0 + cap
    #result = np.zeros(3)

    if ratio > max_cap:
        result = [255.0, 0.0, 0.0]
    elif ratio < min_cap:
        result = [0.0, 0.0, 255.0]
    elif ratio > 1.0:
        other = (ratio - 1.0) / cap * 255.0
        green = 255.0 - other
        result = [other, green, 0.0]
    elif ratio <= 1.0:
        other = (1.0 - ratio) / cap * 255.0
        green = 255.0 - other
        result = [0.0, green, other]
    else:
        print("WARNING: NaN in ratio_to_rgb")

    return [i / 255.0 for i in result]


def export_scene():
    export_scene.exporter.Update()

def export_png():
    writer = vtk.vtkPNGWriter()
    window_to_image_filter = vtk.vtkWindowToImageFilter()
    window_to_image_filter.SetInput(export_png.renWin)
    window_to_image_filter.SetScale(1) # image quality
    window_to_image_filter.SetInputBufferTypeToRGB()
    window_to_image_filter.ReadFrontBufferOff()
    window_to_image_filter.Update()

    writer.SetFileName(f"scene_{calendar.timegm(time.gmtime())}.png")
    writer.SetInputConnection(window_to_image_filter.GetOutputPort())
    writer.Write()

def reset_camera():
    reset_camera.ren.ResetCamera()
    reset_camera.renWin.Render()

def json_get(json_obj, *args):
    for arg in args:
        try:
            return json_obj[arg]
        except:
            pass

"""
Prints which vertex was clicked on when in model mode
"""
def model_callback(caller, ev):
    picker = vtk.vtkPropPicker()
    pos = caller.GetEventPosition()
    picker.PickProp(pos[0], pos[1], callback_function.ren)
    picked_actor = picker.GetActor()
    if picked_actor == model_callback.center_actor:
        pos = np.array(picker.GetPickPosition())
        bestDist = float('inf')
        bestInd = -1
        for i in range(model_callback.vert_mat.shape[0]):
            dist = np.linalg.norm(pos - model_callback.vert_mat[i])
            if dist < bestDist:
                bestDist = dist
                bestInd = i
        callback_function.info_box.setPlainText(f'Picked Vertex: {bestInd}\n{pos}')

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
            try:
                string += str(load_next.descriptions[picked_actor])
            except KeyError:
                string += "No entity description provided"
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
Loads obj file and visualizes it
"""
def load_obj():
    colors = vtk.vtkNamedColors()
    importer = vtk.vtkOBJImporter()
    importer.SetFileName(load_obj.filename)
    importer.SetRenderWindow(load_obj.ren_win)
    importer.Update()
    actor = load_obj.ren.GetActors().GetLastActor()
    if load_obj.light_mode:
        a = 0.27
        actor.GetProperty().SetColor(a, a, a)
    actor.GetProperty().EdgeVisibilityOn()
    reset_camera()

"""
Loads model
"""
def load_model():
    if load_model.done:
        print("No more scenes to render")
        return
    importer = vtk.vtkOBJImporter()
    importer.SetFileName(load_model.filename)
    importer.SetRenderWindow(load_model.ren_win)
    importer.Update()

    all_actors = importer.GetRenderer().GetActors();
    model_actor = all_actors.GetLastActor();
    mesh_in = model_actor.GetMapper().GetInput()

    # Points
    f = open(load_model.filename)
    lines = f.readlines()
    vertices = []
    faces = []
    for line in lines:
        if len(line) and line[0:2] == 'v ':
            vertices.append([float(i) for i in line.strip().split()[1:4]])
        if len(line) and line[0:2] == 'f ':
            faces.append([int(i) for i in np.array(line.replace('//',
                         ' ').split())[[1, 3, 5]]])
    num_vertices = len(vertices)
    vert_mat = np.array(vertices)
    points = vtk.vtkPoints()
    positions = [[], [], []]
    for i in range(0, num_vertices):
        x = vert_mat[i, 0]
        y = vert_mat[i, 1]
        z = vert_mat[i, 2]
        points.InsertNextPoint(x, y, z)
        positions[0].append(x)
        positions[1].append(y)
        positions[2].append(z)
    # Lines
    num_faces = len(faces)
    lines = vtk.vtkCellArray()
    for i in range(0, num_faces):
        face = faces[i]
        for j in range(0, 3):
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, face[j]-1)
            line.GetPointIds().SetId(1, face[(j+1)%3]-1)
            lines.InsertNextCell(line)

    load_model.ren.RemoveActor(all_actors.GetLastActor())
    sphere_source = vtk.vtkSphereSource()
    sphere_source.SetRadius(load_model.sphere_radius)
    sphere_pd = vtk.vtkPolyData()
    sphere_points = points

    lines_pd = vtk.vtkPolyData()
    lines_points = points
    lines_cells = lines

    sphere_pd.SetPoints(sphere_points)
    mapper = vtk.vtkGlyph3DMapper()
    mapper.SetInputData(sphere_pd)
    mapper.SetSourceConnection(sphere_source.GetOutputPort())
    mapper.ScalarVisibilityOff()
    mapper.ScalingOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    load_model.ren.AddActor(actor)

    model_callback.center_actor = actor
    model_callback.vert_mat = vert_mat

    lines_pd.SetPoints(lines_points)
    lines_pd.SetLines(lines_cells)
    tube_filter = vtk.vtkTubeFilter()
    tube_filter.SetInputData(lines_pd);
    tube_filter.SetNumberOfSides(8)
    tube_filter.SetRadius(load_model.tube_radius)
    tube_filter.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(tube_filter.GetOutputPort())
    actor2 = vtk.vtkActor()
    actor2.SetMapper(mapper)
    load_model.ren.AddActor(actor2)

    # Make the axes actor to the correct sizing based on the elements on screen
    cube_axis = vtk.vtkCubeAxesActor()
    cube_axis.SetCamera(load_model.ren.GetActiveCamera());
    mins = [min(i) for i in positions]
    maxs = [max(i) for i in positions]
    dists = [i[0] - i[1] for i in zip(maxs, mins)]
    mins = [i[0] - max(load_model.sphere_radius, i[1] * 0.1)
            for i in zip(mins, dists)]
    maxs = [i[0] + max(load_model.sphere_radius, i[1] * 0.1)
            for i in zip(maxs, dists)]
    bbox = [maxs[i] - mins[i] for i in range(3)]
    load_model.info_box.setPlainText(
            f'Bounding Box Size: {bbox[0]}, {bbox[1]}, {bbox[2]}')
    cube_axis.SetFlyModeToStaticEdges()
    cube_axis.SetBounds((mins[0], maxs[0], mins[1], maxs[1],
        mins[2], maxs[2]))
    load_model.ren.AddActor(cube_axis)

    reset_camera()

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
    sphere_source = vtk.vtkSphereSource()
    sphere_source.SetRadius(load_basic_scene.sphere_radius)
    sphere_pd = vtk.vtkPolyData()
    sphere_points = vtk.vtkPoints()

    lines_pd = vtk.vtkPolyData()
    lines_points = vtk.vtkPoints()
    lines_cells = vtk.vtkCellArray()
    n = 0
    for entity in scene:
        if len(entity) == 6:
            for i in range(3):
                positions[i].append(entity[i+3])
        elif len(entity) == 2:
            entity.append(0)
        for i in range(3):
            positions[i].append(entity[i])
        actor = None
        if len(entity) == 3:
            sphere_points.InsertNextPoint(entity)
        elif len(entity) == 6:
            lines_points.InsertNextPoint(entity[:3])
            lines_points.InsertNextPoint(entity[3:])
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, n)
            line.GetPointIds().SetId(1, n+1)
            lines_cells.InsertNextCell(line)
            n += 2

    sphere_pd.SetPoints(sphere_points)
    mapper = vtk.vtkGlyph3DMapper()
    mapper.SetInputData(sphere_pd)
    mapper.SetSourceConnection(sphere_source.GetOutputPort())
    mapper.ScalarVisibilityOff()
    mapper.ScalingOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    load_basic_scene.ren.AddActor(actor)

    lines_pd.SetPoints(lines_points)
    lines_pd.SetLines(lines_cells)
    tube_filter = vtk.vtkTubeFilter()
    tube_filter.SetInputData(lines_pd);
    tube_filter.SetNumberOfSides(8)
    tube_filter.SetRadius(load_basic_scene.tube_radius)
    tube_filter.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(tube_filter.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    load_basic_scene.ren.AddActor(actor)

    # Make the axes actor to the correct sizing based on the elements on screen
    cube_axis = vtk.vtkCubeAxesActor()
    cube_axis.SetCamera(load_basic_scene.ren.GetActiveCamera());
    mins = [min(i) for i in positions]
    maxs = [max(i) for i in positions]
    dists = [i[0] - i[1] for i in zip(maxs, mins)]
    mins = [i[0] - max(load_basic_scene.sphere_radius, i[1] * 0.1)
            for i in zip(mins, dists)]
    maxs = [i[0] + max(load_basic_scene.sphere_radius, i[1] * 0.1)
            for i in zip(maxs, dists)]
    cube_axis.SetFlyModeToStaticEdges()
    cube_axis.SetBounds((mins[0], maxs[0], mins[1], maxs[1],
        mins[2], maxs[2]))
    #load_basic_scene.ren.AddActor(cube_axis)

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
    scene = json_get(curr, 'entities', 'e')
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
        #try:
        pos = json_get(entity, 'p', 'position')
        for i in range(len(pos)):
            if type(pos[i]) is float:
                load_next.positions[i % 3].append(pos[i])
            else:
                for j in range(len(pos[i])):
                    load_next.positions[j].append(pos[i][j])
            if hold:
                if type(pos) is int:
                    load_next.positions[i % 3].append(pos[i])
                else:
                    for j in range(len(pos[i])):
                        load_next.positions[j].append(pos[i][j])
        #except:
        #    print(entity)
        #    exit(1)
    if "glyph" in load_next.json_doc.keys() and load_next.json_doc["glyph"]:
        sphere_source = vtk.vtkSphereSource()
        #sphere_source.SetRadius(load_next.sphere_radius)
        #sphere_source.SetRadius(.01)
        sphere_pd = vtk.vtkPolyData()
        sphere_points = vtk.vtkPoints()

        lines_pd = vtk.vtkPolyData()
        lines_points = vtk.vtkPoints()
        lines_cells = vtk.vtkCellArray()

        scale_factors_sphere = vtk.vtkFloatArray();
        scale_factors_sphere.SetNumberOfComponents(3);
        scale_factors_sphere.SetName("Scale Factors");
        colors_sphere = vtk.vtkFloatArray();
        colors_sphere.SetNumberOfComponents(4);
        colors_sphere.SetName("Colors");

        scale_factors_line = vtk.vtkFloatArray();
        scale_factors_line.SetNumberOfComponents(1);
        scale_factors_line.SetName("Tube Radii");
        colors_line = vtk.vtkFloatArray();
        colors_line.SetNumberOfComponents(4);
        colors_line.SetName("Colors");

        n = 0
        for entity in scene:
            if 'opacity' not in entity.keys() and 'o' not in entity.keys():
                entity['o'] = 1.0
            if 'color' not in entity.keys() and 'c' not in entity.keys():
                entity['c'] = [1.0, 1.0, 1.0]
            json_type = json_get(entity, 't', 'type')
            if json_type == 'point' or json_type == 'p':
                #source.SetCenter(entity['position'])
                sphere_points.InsertNextPoint(json_get(entity, 'p', 'position'))
                colors_sphere.InsertNextTuple4(*json_get(entity, 'c', 'color'),
                                               json_get(entity, 'o', 'opacity'))
                if 'radius' not in entity.keys() and 'r' not in entity.keys():
                    entity['r'] = load_next.sphere_radius
                scale_factors_sphere.InsertNextTuple3(
                        *[json_get(entity, 'r', 'radius') * 2 for _ in range(3)])
                #actor.GetProperty().SetColor(entity['color'])
                #actor.GetProperty().SetOpacity(entity['opacity'])
            elif json_type == 'vector' or json_type == 'v':
                lines_points.InsertNextPoint(json_get(entity, 'p', 'position')[:3])
                lines_points.InsertNextPoint(json_get(entity, 'p', 'position')[3:])
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, n)
                line.GetPointIds().SetId(1, n+1)
                n += 2
                lines_cells.InsertNextCell(line)
                if 'radius' not in entity.keys() and 'r' not in entity.keys():
                    entity['r'] = load_next.tube_radius
                # This is not working as cell data, only point data,
                # so needs inserted twice
                for _ in range(2):
                    colors_line.InsertNextTuple4(*json_get(entity, 'c', 'color'),
                                                  json_get(entity, 'o', 'opacity'))
                    scale_factors_line.InsertNextTuple1(json_get(entity, 'r', 'radius'))
            elif json_type == 'polyline' or json_type == 'y':
                line = vtk.vtkPolyLine()
                id_count = len(json_get(entity, 'p', 'position'))
                line.GetPointIds().SetNumberOfIds(id_count)
                if 'radius' not in entity.keys() and 'r' not in entity.keys():
                    entity['r'] = load_next.tube_radius
                for i in range(id_count):
                    pt = json_get(entity, 'p', 'position')[i]
                    lines_points.InsertNextPoint(pt)
                    line.GetPointIds().SetId(i, n)
                    n += 1
                    colors_line.InsertNextTuple4(*json_get(entity, 'c', 'color'),
                                                  json_get(entity, 'o', 'opacity'))
                    scale_factors_line.InsertNextTuple1(json_get(entity, 'r', 'radius'))
                lines_cells.InsertNextCell(line)

        sphere_pd.SetPoints(sphere_points)
        mapper = vtk.vtkGlyph3DMapper()

        sphere_pd.GetPointData().AddArray(colors_sphere);
        sphere_pd.GetPointData().AddArray(scale_factors_sphere);
        mapper.SetInputData(sphere_pd)
        mapper.SetSourceConnection(sphere_source.GetOutputPort())
        mapper.SetScalarModeToUsePointFieldData()

        mapper.SelectColorArray("Colors");
        mapper.SetColorMode(2)

        mapper.SetScaleModeToScaleByVectorComponents()
        mapper.SetScaleArray("Scale Factors")
        mapper.Update()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        load_next.ren.AddActor(actor)
        load_next.actors.append(actor)

        lines_pd.SetPoints(lines_points)
        lines_pd.SetLines(lines_cells)
        lines_pd.GetPointData().AddArray(colors_line);
        lines_pd.GetPointData().SetScalars(scale_factors_line);
        lines_pd.GetPointData().SetActiveScalars("Tube Radii")
        tube_filter = vtk.vtkTubeFilter()
        tube_filter.SetInputData(lines_pd)
        tube_filter.SetNumberOfSides(8)
        tube_filter.SetVaryRadiusToVaryRadiusByAbsoluteScalar()
        tube_filter.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SelectColorArray("Colors");
        mapper.SetColorMode(2)
        mapper.ScalarVisibilityOn()
        mapper.SetScalarModeToUsePointFieldData()
        mapper.SetInputConnection(tube_filter.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        load_next.ren.AddActor(actor)
        load_next.actors.append(actor)

    #linesPolyData->GetCellData()->SetScalars(colors);
    #vtkNew<vtkTubeFilter> tubeFilter;
    #tubeFilter->SetInputData(linesPolyData);
    #tubeFilter->SetNumberOfSides(8);
    #tubeFilter->SetRadius(radius);
    #tubeFilter->Update();
    #vtkNew<vtkPolyDataMapper> mapper;
    #mapper->SetInputConnection(tubeFilter->GetOutputPort());
    #mapper->SetColorMode(2);

    #vtkNew<vtkActor> actor;
    #actor->SetMapper(mapper);
    #actor->GetProperty()->SetLineWidth(4);
    else:
        for entity in scene:
            actor = vtk.vtkActor()
            mapper = vtk.vtkPolyDataMapper()
            if 'opacity' not in entity.keys() and 'o' not in entity.keys():
                entity['o'] = 1.0
            if 'color' not in entity.keys() and 'c' not in entity.keys():
                entity['c'] = [1.0, 1.0, 1.0]
            if 'description' not in entity.keys() and 'd' not in entity.keys():
                entity['d'] = "No entity description provided"
            json_type = json_get(entity, 't', 'type')
            if json_type == 'point' or json_type == 'p':
                if 'radius' not in entity.keys() and 'r' not in entity.keys():
                    entity['r'] = load_next.sphere_radius
                source = vtk.vtkSphereSource()
                source.SetRadius(json_get(entity, 'r', 'radius'))
                source.SetCenter(json_get(entity, 'p', 'position'))
                mapper.SetInputConnection(source.GetOutputPort())
            elif json_type == 'vector' or json_type == 'v':
                if 'radius' not in entity.keys() and 'r' not in entity.keys():
                    entity['r'] = load_next.tube_radius
                line_source = vtk.vtkLineSource()
                line_source.SetPoint1(json_get(entity, 'p', 'position')[:3])
                line_source.SetPoint2(json_get(entity, 'p', 'position')[3:])
                line_source.SetResolution(6)
                line_source.Update()
                tube_filter = vtk.vtkTubeFilter()
                tube_filter.SetInputConnection(line_source.GetOutputPort())
                tube_filter.SetNumberOfSides(8)
                tube_filter.SetRadius(json_get(entity, 'r', 'radius'))
                tube_filter.Update()
                mapper.SetInputConnection(tube_filter.GetOutputPort())
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(json_get(entity, 'c', 'color'))
            actor.GetProperty().SetOpacity(json_get(entity, 'o', 'opacity'))
            load_next.ren.AddActor(actor)
            load_next.actors.append(actor)
            if hold:
                load_next.hold_actors.append(actor)
            if actor:
                load_next.descriptions[actor] = json_get(entity, 'd', 'description')

    # Make the axes actor to the correct sizing based on the elements on screen
    cube_axis = vtk.vtkCubeAxesActor()
    cube_axis.SetCamera(load_next.ren.GetActiveCamera());
    mins = [min(i) for i in load_next.positions]
    maxs = [max(i) for i in load_next.positions]
    dists = [i[0] - i[1] for i in zip(maxs, mins)]
    mins = [i[0] - max(load_next.sphere_radius, i[1] * 0.1)
            for i in zip(mins, dists)]
    maxs = [i[0] + max(load_next.sphere_radius, i[1] * 0.1)
            for i in zip(maxs, dists)]
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

    from pycimg import CImg
    yellow = np.array([255.0, 255.0, 0.0]).astype(np.float32)

    writer = vtk.vtkPNGWriter()

    window_to_image_filter = vtk.vtkWindowToImageFilter()
    window_to_image_filter.SetInput(load_next.vtkWidget.GetRenderWindow());
    window_to_image_filter.SetScale(1);
    window_to_image_filter.SetInputBufferTypeToRGB();
    window_to_image_filter.ReadFrontBufferOff();
    window_to_image_filter.Update();

    writer.SetFileName('test.png');
    writer.SetInputConnection(window_to_image_filter.GetOutputPort());
    writer.Write();

    img = CImg('test.png')
    img.draw_text(x0=10, y0=img.height - 40, text=f"kA90: {1.0:.2}, kA120: {1.0:.2}, kLinear: {1.0:.2}, Epochs: {0}",
            foreground_color=yellow, background_color=np.array([0.0,0.0,0.0]).astype(np.float32), opacity=1.0, font_height=32);
    img.save_png('test2.png');
    exit(0)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
