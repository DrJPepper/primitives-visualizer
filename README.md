# Primitives Visualizer

![Screenshot 1](https://www.cs.drexel.edu/~jcp353@drexel.edu/images/s1.png "Screenshot 1")
**TODO**: Add more screenshots/gifs

This program visualizes basic 3D geometric primitives (currently, tubes and
spheres) in a VTK window as they are described in a JSON input file. Its purpose
is to allow for the visual analysis, debugging, etc. of 3D modeling and
simulation programs without needing to write special purpose code for every one
off task.

## Input
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

## Example JSON

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

## Running
`python3 prim_visualizer.py`, with the following optional arguments:

usage: PrimitivesVisualizer [-h] [-f FILENAME] [-t TUBE_RADIUS] [-s SPHERE_RADIUS]

Visualizes 3D geometry from a JSON file

options:
  -h, --help            show this help message and exit
  -f FILENAME, --filename FILENAME
  -t TUBE_RADIUS, --tube-radius TUBE_RADIUS
  -s SPHERE_RADIUS, --sphere-radius SPHERE_RADIUS

Filename can also be specified in ./default_input.txt

## Dependencies
Python (at least 3.4 I think), VTK, Qt5, PyQt5

## Mac Install Instructions
1. Install dependencies:
    1. With [brew](https://brew.sh/): `brew install vtk qt@5 python@3.11`
    1. Without brew:
        1. Install the latest version of python from
        [https://www.python.org/downloads/](https://www.python.org/downloads/)
        1. Install VTK from [https://vtk.org/download/](https://vtk.org/download/)
        1. Install Qt5 (**not** Qt6) from
        [https://doc.qt.io/qt-5/macos.html](https://doc.qt.io/qt-5/macos.html)
        1. Open your terminal emulator
        1. Run `/usr/local/bin/pip3 install pyqt5`
        1. Feel free to add `/usr/local/bin` to your PATH if it isn't there already
1. Clone this repo via `git clone
   https://github.com/DrJPepper/primitives-visualizer.git`
    1. Your may be prompted to install CLI dev tools, be sure to do that if
       asked
1. `cd primitives-visualizer`
1. Download the following example file, either via `wget` or web browser and
   place it in the `primitives-visualizer` directory: [example\_vis.json](https://www.cs.drexel.edu/~jcp353@drexel.edu/files/example\_vis.json)
1. Run `python3 prim_visualizer.py -f example_vis.json`

## Example C++ code to generate the JSON
**TODO**
