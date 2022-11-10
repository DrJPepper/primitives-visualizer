# Primitives Visualizer

**TODO**: Add some screenshots/gifs

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
                ]
                "hold": true,
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

## Example C++ code to generate the JSON
**TODO**
