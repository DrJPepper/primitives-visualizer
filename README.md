# Primitives Visualizer

<p float="left" align="center">
  <img src="https://drjpepper.github.io/images/prim_viz/s1.png" width="48%" />
  <img src="https://drjpepper.github.io/images/prim_viz/s2.png" width="50%" /> 
  <img src="https://drjpepper.github.io/images/prim_viz/scene.png" width="70%" /> 
</p>

This program visualizes basic 3D geometric primitives (tubes, spheres and
triangle meshes) using VTK. Inputs can be provided as either a JSON file for
more complex scenes, a basic text file for just points and lines, an OBJ file,
or via HTTP calls to a built-in API server. Its purpose is to allow for the
visual analysis, debugging, etc. of 3D modeling and simulation programs without
needing to write special purpose code for every one off task.

## Dependencies

* Python (at least 3.4)
* Numpy
* VTK
* Qt6
* PyQt6
* For the web API:
    * FastAPI
    * Uvicorn

## Running

`python3 prim_visualizer.py`, with the following optional arguments:

    usage: python3 prim_visualizer.py [-h] [-l | --light-mode | --no-light-mode] [-m | --model-mode | --no-model-mode]
                                [-o | --obj-mode | --no-obj-mode] [-b | --basic-mode | --no-basic-mode]
                                [-w | --server-mode | --no-server-mode] [-r | --render-mode | --no-render-mode]
                                [-c | --scalar-field-mode | --no-scalar-field-mode] [-n | --dont-reset | --no-dont-reset]
                                [-f FILENAME] [-t TUBE_RADIUS] [-s SPHERE_RADIUS]

    Visualizes 3D geometry from a JSON file

    options:
      -h, --help            show this help message and exit
      -l, --light-mode, --no-light-mode
      -m, --model-mode, --no-model-mode
      -o, --obj-mode, --no-obj-mode
      -b, --basic-mode, --no-basic-mode
      -w, --server-mode, --no-server-mode
      -r, --render-mode, --no-render-mode
      -c, --scalar-field-mode, --no-scalar-field-mode
      -n, --dont-reset, --no-dont-reset
      -f, --filename FILENAME
      -t, --tube-radius TUBE_RADIUS
      -s, --sphere-radius SPHERE_RADIUS

## Input

There are four input types: basic text file, JSON file, OBJ file and HTTP calls.

### Basic Text

Input can be provided as a list of points and lines in a text file, with each
entity separated by a new line. 2 or 3 numbers indicate a point, and 4 or 6
numbers indicate a line. Entities can be colored by adding a
[named color](https://www.w3.org/TR/css-color-3/) to the end of a line in the
file. Lines starting with a '#' will be ignored as comments.

Below is an example of a "basic text" input. At the top are two lines, followed
by several points. The points are colored, while the lines are left as the
default. 

    -20.8726 -25.3649 -18.2709 -26.6217  25.8597 -17.8455
     28.7377   23.365 -19.3347  30.9912  22.7508 -19.2227
    -20.8726 -25.3649 -18.2709 Green
    47.5995 40.7997 13.5991 Red
    -26.6217  25.8597 -17.8455 Green
    -19.6442  41.6037  12.3928 Red
     28.7377   23.365 -19.3347 Green
     43.978 9.88262 56.2931 Red
     30.9912  22.7508 -19.2227 Green
    -13.1368  8.48966   55.879 Red

![Basic text input](https://drjpepper.github.io/images/prim_viz/basic.png)

### JSON

Input must be supplied in the form of a JSON file. The format for the file needs
to be as follows:

- `"reset"`: A Boolean that specifies whether to default reset the scene after
  each new entity is loaded.
- `"list"`: The list of "entries" that are to be visualized one after the other.
  These entities need to contain the following properties:
    - `"color"`: An array of 3 floats between 0 and 1 corresponding to RGB.
    - `"description"`: A description of the entity to be shown when it is
      clicked on.
    - `"opacity"`: A floating point opacity value between 0 and 1 (with 0 being
      invisible and 1 being fully opaque.
    - `"position"`: An array of either 3 floats for a sphere of 6 floats for a
      tube that correspond to the centroid of the sphere or the endpoints of the
      central axis of the tube respectively.
    - `"type"`: Either `"point"` or `"vector"`.

  These entities may optionally contain:

    - `"reset"`: A Boolean that overrides the global `reset` key.
    - `"hold"`: A Boolean that can be used to tell the program to hold the
      primitives in this entry even if a reset occurs.

A simple example of this format with two scenes, one with two lines and the
other with two points, which add on to each other is as follows:

```
{
    "list": [
        {
            "entities": [
                {
                    "color": [
                        1.0,
                        1.0,
                        1.0
                    ],
                    "description": "Edge with rest length 0.999978\nIndex: 347",
                    "opacity": 1.0,
                    "position": [
                        13.856,
                        18.0,
                        0.0,
                        14.722,
                        18.5,
                        0.0
                    ],
                    "type": "vector"
                },
                {
                    "color": [
                        1.0,
                        1.0,
                        1.0
                    ],
                    "description": "Edge with rest length 0.999978\nIndex: 723",
                    "opacity": 1.0,
                    "position": [
                        13.856,
                        18.0,
                        1.0,
                        14.722,
                        18.5,
                        1.0
                    ],
                    "type": "vector"
                }
            ],
            "hold": true
        },
        {
            "entities": [
                {
                    "color": [
                        1.0,
                        1.0,
                        1.0
                    ],
                    "description": "Vertex at: 0 0 0\n\nIndex: 0",
                    "opacity": 1.0,
                    "position": [
                        0.0,
                        0.0,
                        0.0
                    ],
                    "type": "point"
                },
                {
                    "color": [
                        1.0,
                        1.0,
                        1.0
                    ],
                    "description": "Vertex at: 1.732     0     0\n\nIndex: 1",
                    "opacity": 1.0,
                    "position": [
                        1.732,
                        0.0,
                        0.0
                    ],
                    "type": "point"
                }
            ]
        }
    ],
    "reset": true
}
```

<p float="left">
  <img src="https://drjpepper.github.io/images/prim_viz/json1.png" width="49%" />
  <img src="https://drjpepper.github.io/images/prim_viz/json2.png" width="49%" /> 
</p>

### OBJ

OBJ files can be visualized normally via the `-o` flag, or as their edges and vertices with `-m`. In `-m` model, vertices can be picked to display their indices.

![Vertex picking](https://drjpepper.github.io/images/prim_viz/model_mode.png)

### API

A web API can be started using the `-w` flag. Once started, the `/update_scene` route can be called to change the contents of the scene using the JSON scene description format. Scenes need placed in the POST body. An example of a python function which uses the API is:

    def init_viz(self, correct=None):
        pld = {'action': 'init', 'scene': []}
        for i in self.dataset.cells.keys():
            c = self.dataset.cells[i]
            pld['scene'].append({'type': 'point', 'position': c.center,
                                 'opacity': 0.5, 'color':
                                 ratio_to_rgb(self.cells[i] / 5.0)})
        if correct:
            for i, c in correct.items():
                color = None
                if len(c) == 2:
                    if sum(c) == 0:
                        color = [1.0, 0.0, 0.0]
                    elif sum(c) == 1:
                        color = [1.0, 1.0, 0.0]
                    else:
                        color = [0.0, 1.0, 0.0]
                else:
                    if c[0]:
                        color = [0.0, 1.0, 0.0]
                    else:
                        color = [1.0, 0.0, 0.0]
                pld['scene'].append({'type': 'vector', 'color': color,
                                     'position':
                                     self.dataset.edge_positions[i]})
        else:
            for i in self.dataset.edge_positions.keys():
                pld['scene'].append({'type': 'vector', 'position':
                                     self.dataset.edge_positions[i]})
        try:
            requests.post("http://127.0.0.1:8000/update_scene", json=pld)
        except requests.exceptions.ConnectionError:
            print("Port 8000 closed, disabling calls to GUI server")

<p float="left">
  <img src="https://drjpepper.github.io/images/prim_viz/web1.png" width="49%" />
  <img src="https://drjpepper.github.io/images/prim_viz/web2.png" width="49%" /> 
</p>

Updating the colors of a scene dynamically via the API.
