# -*- coding: utf-8 -*-
"""
Created on Sat Nov 21 15:03:54 2020

@author: Lucas Borboleta
"""

_COPYRIGHT_AND_LICENSE = """
JERSI-DRAWER-TK draws a vectorial picture of JERSI boardgame state from an abstract state.

Copyright (C) 2020 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""


import enum
import math
import os
import re
import subprocess

import tkinter as tk
from tkinter import font
from tkinter import ttk
from tkinter import filedialog

import PIL


class JersiError(Exception):
    """Customized exception dedicated to all classes of JERSI"""

    def __init__(self, message):
        """JERSI exception records an explaining text message"""
        Exception.__init__(self)
        self.message = message


def jersi_assert(condition, message):
    """If condition fails (is False) then raise a JERSI exception
    together with the explaining message"""
    if not condition:
        raise JersiError(message)


class TinyVector:
    """Lightweight algebra on 2D vectors, inspired by numpy ndarray."""

    __slots__ = ("__x", "__y")

    def __init__(self, xy_pair=None):
        if xy_pair is None:
            self.__x = 0.
            self.__y = 0.

        else:
            self.__x = float(xy_pair[0])
            self.__y = float(xy_pair[1])


    def __repr__(self):
        return str(self)


    def __str__(self):
        return str((self.__x, self.__y))


    def __getitem__(self, key):
        if key == 0:
            return self.__x

        elif key == 1:
            return self.__y

        else:
            raise IndexError()


    def __neg__(self):
        return TinyVector((-self.__x , -self.__y))


    def __pos__(self):
        return TinyVector((self.__x , self.__y))


    def __add__(self, other):
        if isinstance(other, TinyVector):
            return TinyVector((self.__x + other.__x, self.__y + other.__y))

        elif isinstance(other, (int, float)):
            return TinyVector((self.__x + other, self.__y + other))

        else:
            raise NotImplementedError()


    def __sub__(self, other):
        if isinstance(other, TinyVector):
            return TinyVector((self.__x - other.__x, self.__y - other.__y))

        elif isinstance(other, (int, float)):
            return TinyVector((self.__x - other, self.__y - other))

        else:
            raise NotImplementedError()


    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return TinyVector((self.__x*other, self.__y*other))

        else:
            raise NotImplementedError()


    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return TinyVector((self.__x/other, self.__y/other))

        else:
            raise NotImplementedError()


    def __radd__(self, other):
        return self.__add__(other)


    def __rmul__(self, other):
        return self.__mul__(other)


    def __rtruediv__(self, other):
        return self.__div__(other)


    def __rsub__(self, other):
        if isinstance(other, TinyVector):
            return TinyVector((-self.__x + other.__x, -self.__y + other.__y))

        elif isinstance(other, (int, float)):
            return TinyVector((-self.__x + other, -self.__y + other))

        else:
            raise NotImplementedError()


    @staticmethod
    def inner(that, other):
        if isinstance(that, TinyVector) and isinstance(other, TinyVector):
            return (that.__x*other.__x + that.__y*other.__y)

        else:
            raise NotImplementedError()


    @staticmethod
    def norm(that):
        if isinstance(that, TinyVector):
            return math.sqrt(that.__x*that.__x + that.__y*that.__y)

        else:
            raise NotImplementedError()

JERSI_HOME = os.path.abspath(os.path.dirname(__file__))

JERSI_STATE_FILE = os.path.join(JERSI_HOME, "states", "import", "jersi-state-initial.txt")

JERSI_ICON_FILE = os.path.join(JERSI_HOME, 'jersi.ico')
JERSI_IMAGE_FILE = os.path.join(JERSI_HOME, 'jersi.png')
if not os.path.isfile(JERSI_ICON_FILE):
    JERSI_ICON_SIZES = [(16,16), (32, 32), (48, 48), (64,64)]
    PIL.Image.open(JERSI_IMAGE_FILE).save(JERSI_ICON_FILE, sizes=JERSI_ICON_SIZES)

CANVAS_RATIO = 1
CANVAS_HEIGHT = 600
CANVAS_WIDTH = int(CANVAS_HEIGHT * CANVAS_RATIO)

USE_JERSI_PURE_STYLE = True

# number of hexagons to draw
NX = 9 + 2
NY = 9

# Draw faces of cubes ?
# If 'False' the just display letter representing the type of the cube
DRAW_CUBE_FACES = True

# Draw extra hexagons and extra cubes (reserve) ?
DRAW_EXTRA = True

# Hexagon geometrical data
HEXA_VERTEX_COUNT = 6
HEXA_SIDE_ANGLE = 2*math.pi/HEXA_VERTEX_COUNT
HEXA_WIDTH = min(CANVAS_HEIGHT, CANVAS_WIDTH) / max(NX, NY)
HEXA_SIDE = HEXA_WIDTH*math.tan(HEXA_SIDE_ANGLE/2)

HEXA_DELTA_Y = math.sqrt(HEXA_SIDE**2 -(HEXA_WIDTH/2)**2)

# Cube (square) geometrical data
CUBE_VERTEX_COUNT = 4
CUBE_SIDE_ANGLE = math.pi/2

# Font used for text in the canvas
FONT_FAMILY = 'Calibri'
FONT_LABEL_SIZE = int(0.30*HEXA_SIDE) # size for 'e5', 'f5' ...
FONT_FACE_SIZE = int(0.50*HEXA_SIDE)  # size for 'K', 'F' ...

# Geometrical widths
CUBE_LINE_WIDTH = int(0.05*HEXA_SIDE)
HEXA_LINE_WIDTH = int(0.02*HEXA_SIDE)

# Origin of the orthonormal x-y frame and the oblic u-v frame
ORIGIN = TinyVector((CANVAS_WIDTH/2, CANVAS_HEIGHT/2))

# Unit vectors of the orthonormal x-y frame
UNIT_X = TinyVector((1, 0))
UNIT_Y = TinyVector((0, -1))

# Unit vectors of the oblic u-v frame
UNIT_U = UNIT_X
UNIT_V = math.cos(HEXA_SIDE_ANGLE)*UNIT_X + math.sin(HEXA_SIDE_ANGLE)*UNIT_Y

# Abstract state of the board
STATE = dict()


def rgb_color(rgb):
    (red, green, blue) = rgb
    return '#%02x%02x%02x' % (red, green, blue)


class HexagonColor(enum.Enum):
    INNER = rgb_color((166, 109, 60))
    MAIN = rgb_color((242, 202, 128))
    OUTER = rgb_color((191, 89, 52))
    EXTRA = rgb_color((191, 184, 180))


class CubeColor(enum.Enum):
    BLACK = enum.auto()
    WHITE = enum.auto()


class CubeConfig(enum.Enum):
    BOTTOM = enum.auto()
    SINGLE = enum.auto()
    TOP = enum.auto()


class CubeType(enum.Enum):
    KING = 'K'
    FOOL = 'F'
    PAPER = 'P'
    ROCK = 'R'
    SCISSORS = 'S'
    MOUNTAIN = 'M'
    WISE = 'W'


CUBE_COLORED_TYPES = dict()

CUBE_COLORED_TYPES['K'] = (CubeType.KING, CubeColor.WHITE)
CUBE_COLORED_TYPES['F'] = (CubeType.FOOL, CubeColor.WHITE)
CUBE_COLORED_TYPES['R'] = (CubeType.ROCK, CubeColor.WHITE)
CUBE_COLORED_TYPES['P'] = (CubeType.PAPER, CubeColor.WHITE)
CUBE_COLORED_TYPES['S'] = (CubeType.SCISSORS, CubeColor.WHITE)
CUBE_COLORED_TYPES['M'] = (CubeType.MOUNTAIN, CubeColor.WHITE)
CUBE_COLORED_TYPES['W'] = (CubeType.WISE, CubeColor.WHITE)


CUBE_COLORED_TYPES['k'] = (CubeType.KING, CubeColor.BLACK)
CUBE_COLORED_TYPES['f'] = (CubeType.FOOL, CubeColor.BLACK)
CUBE_COLORED_TYPES['r'] = (CubeType.ROCK, CubeColor.BLACK)
CUBE_COLORED_TYPES['p'] = (CubeType.PAPER, CubeColor.BLACK)
CUBE_COLORED_TYPES['s'] = (CubeType.SCISSORS, CubeColor.BLACK)
CUBE_COLORED_TYPES['m'] = (CubeType.MOUNTAIN, CubeColor.BLACK)
CUBE_COLORED_TYPES['w'] = (CubeType.WISE, CubeColor.BLACK)


class Hexagon:

    alls = dict()

    def __init__(self, label, position_uv, color, is_extra=False, extra_shift=None):
        jersi_assert(is_extra == (extra_shift is not None),
                     "is_extra and extra_shift not consisten for label '%s'" % label)

        self.label = label
        self.position_uv = position_uv
        self.color = color
        self.is_extra = is_extra
        self.extra_shift = extra_shift

    @staticmethod
    def add(label, position_uv, color, is_extra=False, extra_shift=None):
        jersi_assert(label not in Hexagon.alls,
                     "no hexagon with label '%s'" % label)

        Hexagon.alls[label] = Hexagon(label, position_uv, color, is_extra, extra_shift)


# Row "a"
Hexagon.add('a1', (-1, -4), HexagonColor.OUTER.value)
Hexagon.add('a2', (-0, -4), HexagonColor.OUTER.value)
Hexagon.add('a3', (1, -4), HexagonColor.OUTER.value)
Hexagon.add('a4', (2, -4), HexagonColor.OUTER.value)
Hexagon.add('a5', (3, -4), HexagonColor.OUTER.value)
Hexagon.add('a6', (4, -4), HexagonColor.OUTER.value)
Hexagon.add('a7', (5, -4), HexagonColor.OUTER.value)

Hexagon.add('a', (6, -4), HexagonColor.EXTRA.value, is_extra=True,
            extra_shift=0.75*HEXA_WIDTH*UNIT_X - HEXA_DELTA_Y*UNIT_Y)

# Row "b"
Hexagon.add('b1', (-2, -3), HexagonColor.OUTER.value)
Hexagon.add('b2', (-1, -3), HexagonColor.MAIN.value)
Hexagon.add('b3', (0, -3), HexagonColor.MAIN.value)
Hexagon.add('b4', (1, -3), HexagonColor.MAIN.value)
Hexagon.add('b5', (2, -3), HexagonColor.MAIN.value)
Hexagon.add('b6', (3, -3), HexagonColor.MAIN.value)
Hexagon.add('b7', (4, -3), HexagonColor.MAIN.value)
Hexagon.add('b8', (5, -3), HexagonColor.OUTER.value)

Hexagon.add('b', (6, -3), HexagonColor.EXTRA.value, is_extra=True,
            extra_shift=0.25*HEXA_WIDTH*UNIT_X)

# Row "c"
Hexagon.add('c1', (-2, -2), HexagonColor.OUTER.value)
Hexagon.add('c2', (-1, -2), HexagonColor.MAIN.value)
Hexagon.add('c3', (0, -2), HexagonColor.INNER.value)
Hexagon.add('c4', (1, -2), HexagonColor.INNER.value)
Hexagon.add('c5', (2, -2), HexagonColor.INNER.value)
Hexagon.add('c6', (3, -2), HexagonColor.MAIN.value)
Hexagon.add('c7', (4, -2), HexagonColor.OUTER.value)

Hexagon.add('c', (5, -2), HexagonColor.EXTRA.value, is_extra=True,
            extra_shift=0.75*HEXA_WIDTH*UNIT_X + HEXA_DELTA_Y*UNIT_Y)

# Row "d"
Hexagon.add('d1', (-3, -1), HexagonColor.OUTER.value)
Hexagon.add('d2', (-2, -1), HexagonColor.MAIN.value)
Hexagon.add('d3', (-1, -1), HexagonColor.INNER.value)
Hexagon.add('d4', (0, -1), HexagonColor.MAIN.value)
Hexagon.add('d5', (1, -1), HexagonColor.MAIN.value)
Hexagon.add('d6', (2, -1), HexagonColor.INNER.value)
Hexagon.add('d7', (3, -1), HexagonColor.MAIN.value)
Hexagon.add('d8', (4, -1), HexagonColor.OUTER.value)

# Row "e"
Hexagon.add('e1', (-4, 0), HexagonColor.OUTER.value)
Hexagon.add('e2', (-3, 0), HexagonColor.MAIN.value)
Hexagon.add('e3', (-2, 0), HexagonColor.INNER.value)
Hexagon.add('e4', (-1, 0), HexagonColor.MAIN.value)
Hexagon.add('e5', (0, 0), HexagonColor.INNER.value)
Hexagon.add('e6', (1, 0), HexagonColor.MAIN.value)
Hexagon.add('e7', (2, 0), HexagonColor.INNER.value)
Hexagon.add('e8', (3, 0), HexagonColor.MAIN.value)
Hexagon.add('e9', (4, 0), HexagonColor.OUTER.value)

# Row "f"
Hexagon.add('f1', (-4, 1), HexagonColor.OUTER.value)
Hexagon.add('f2', (-3, 1), HexagonColor.MAIN.value)
Hexagon.add('f3', (-2, 1), HexagonColor.INNER.value)
Hexagon.add('f4', (-1, 1), HexagonColor.MAIN.value)
Hexagon.add('f5', (0, 1), HexagonColor.MAIN.value)
Hexagon.add('f6', (1, 1), HexagonColor.INNER.value)
Hexagon.add('f7', (2, 1), HexagonColor.MAIN.value)
Hexagon.add('f8', (3, 1), HexagonColor.OUTER.value)

# Row "g"
Hexagon.add('g', (-5, 2), HexagonColor.EXTRA.value, is_extra=True,
                        extra_shift=-0.75*HEXA_WIDTH*UNIT_X - HEXA_DELTA_Y*UNIT_Y)

Hexagon.add('g1', (-4, 2), HexagonColor.OUTER.value)
Hexagon.add('g2', (-3, 2), HexagonColor.MAIN.value)
Hexagon.add('g3', (-2, 2), HexagonColor.INNER.value)
Hexagon.add('g4', (-1, 2), HexagonColor.INNER.value)
Hexagon.add('g5', (0, 2), HexagonColor.INNER.value)
Hexagon.add('g6', (1, 2), HexagonColor.MAIN.value)
Hexagon.add('g7', (2, 2), HexagonColor.OUTER.value)

# Row "h"
Hexagon.add('h', (-6, 3), HexagonColor.EXTRA.value, is_extra=True,
                        extra_shift=-0.25*HEXA_WIDTH*UNIT_X)

Hexagon.add('h1', (-5, 3), HexagonColor.OUTER.value)
Hexagon.add('h2', (-4, 3), HexagonColor.MAIN.value)
Hexagon.add('h3', (-3, 3), HexagonColor.MAIN.value)
Hexagon.add('h4', (-2, 3), HexagonColor.MAIN.value)
Hexagon.add('h5', (-1, 3), HexagonColor.MAIN.value)
Hexagon.add('h6', (0, 3), HexagonColor.MAIN.value)
Hexagon.add('h7', (1, 3), HexagonColor.MAIN.value)
Hexagon.add('h8', (2, 3), HexagonColor.OUTER.value)

# Row "i"
Hexagon.add('i', (-6, 4), HexagonColor.EXTRA.value, is_extra=True,
                        extra_shift=-0.75*HEXA_WIDTH*UNIT_X + HEXA_DELTA_Y*UNIT_Y)

Hexagon.add('i1', (-5, 4), HexagonColor.OUTER.value)
Hexagon.add('i2', (-4, 4), HexagonColor.OUTER.value)
Hexagon.add('i3', (-3, 4), HexagonColor.OUTER.value)
Hexagon.add('i4', (-2, 4), HexagonColor.OUTER.value)
Hexagon.add('i5', (-1, 4), HexagonColor.OUTER.value)
Hexagon.add('i6', (0, 4), HexagonColor.OUTER.value)
Hexagon.add('i7', (1, 4), HexagonColor.OUTER.value)


def draw_king_face(canvas, cube_center, cube_vertices, face_color):
    pass


def draw_fool_face(canvas, cube_center, cube_vertices, face_color):


    def rotate_90_degrees(vector):
        """Rotate 90 degrees counter clock"""
        projection_x = TinyVector.inner(vector, UNIT_X)
        projection_y = TinyVector.inner(vector, UNIT_Y)
        rotated_unit_x = UNIT_Y
        rotated_unit_y = -UNIT_X
        return projection_x*rotated_unit_x + projection_y*rotated_unit_y


    def square_for_circle_by_two_points(point_1, point_2):
        """Return two points of the square enclosing the circle passing by to given points"""
        square_center = 0.5*(point_1 + point_2)
        square_point_1 = point_1 + rotate_90_degrees(point_1 - square_center)
        square_point_2 = point_2 + rotate_90_degrees(point_2 - square_center)
        return (square_point_1, square_point_2)


    face_vertex_NE = 0.5*cube_center + 0.5*cube_vertices[0]
    face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
    face_vertex_SW = 0.5*cube_center + 0.5*cube_vertices[2]
    face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

    face_vertex_N = 0.5*(face_vertex_NW + face_vertex_NE)
    face_vertex_S = 0.5*(face_vertex_SW + face_vertex_SE)

    face_vertex_NC = 0.5*(face_vertex_N + cube_center)
    face_vertex_SC = 0.5*(face_vertex_S + cube_center)

    cube_side = TinyVector.norm(face_vertex_NW - face_vertex_NE)

    # little angular overlap to ensure coninuity bewteen arcs
    angle_epsilon = 0.01*180

    (p1, p2) = square_for_circle_by_two_points(cube_center, face_vertex_SC)
    canvas.create_arc(*p1, *p2,
                      start=90,
                      extent=180,
                      fill='',
                      outline=face_color,
                      style=tk.ARC,
                      width=CUBE_LINE_WIDTH)

    (p1, p2) = square_for_circle_by_two_points(face_vertex_NC, face_vertex_SC)
    canvas.create_arc(*p1, *p2,
                      start=-90 - angle_epsilon,
                      extent=180 + angle_epsilon,
                      fill='',
                      outline=face_color,
                      style=tk.ARC,
                      width=CUBE_LINE_WIDTH)

    (p1, p2) = square_for_circle_by_two_points(face_vertex_NC, face_vertex_S)
    canvas.create_arc(*p1, *p2,
                      start=90 - angle_epsilon,
                      extent=180 + angle_epsilon,
                      fill='',
                      outline=face_color,
                      style=tk.ARC,
                      width=CUBE_LINE_WIDTH)

    (p1, p2) = square_for_circle_by_two_points(face_vertex_N, face_vertex_S)
    canvas.create_arc(*p1, *p2,
                      start=-90 - angle_epsilon,
                      extent=180 + 45 + angle_epsilon,
                      fill='',
                      outline=face_color,
                      style=tk.ARC,
                      width=CUBE_LINE_WIDTH)

    # >> canvas doesn't provide rounded capstype for arc
    # >> so let add one small circle at each edge of the spiral

    # add small circle at the inner edge of the spiral

    inner_edge_top = cube_center + CUBE_LINE_WIDTH*0.5*UNIT_Y
    edge_edge_bottom = cube_center - CUBE_LINE_WIDTH*0.5*UNIT_Y

    (p1, p2) = square_for_circle_by_two_points(inner_edge_top, edge_edge_bottom)
    canvas.create_oval(*p1, *p2,
                       fill=face_color,
                       outline='')

    # add small circle at the outer edge of the spiral

    outer_edge_middle = cube_center + cube_side/2*(UNIT_Y - UNIT_X)/math.sqrt(2)

    outer_edge_top = outer_edge_middle + CUBE_LINE_WIDTH*0.5*UNIT_Y
    outer_edge_bottom = outer_edge_middle - CUBE_LINE_WIDTH*0.5*UNIT_Y

    (p1, p2) = square_for_circle_by_two_points(outer_edge_top, outer_edge_bottom)
    canvas.create_oval(*p1, *p2,
                       fill=face_color,
                       outline='')


def draw_paper_face(canvas, cube_center, cube_vertices, face_color):

    face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
    face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

    canvas.create_rectangle(*face_vertex_NW, *face_vertex_SE,
                            fill='',
                            outline=face_color,
                            width=CUBE_LINE_WIDTH)


def draw_rock_face(canvas, cube_center, cube_vertices, face_color):

    face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
    face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

    canvas.create_oval(*face_vertex_NW, *face_vertex_SE,
                       fill='',
                       outline=face_color,
                       width=CUBE_LINE_WIDTH)


def draw_scissors_face(canvas, cube_center, cube_vertices, face_color):

    face_vertex_NE = 0.5*cube_center + 0.5*cube_vertices[0]
    face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
    face_vertex_SW = 0.5*cube_center + 0.5*cube_vertices[2]
    face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

    canvas.create_line(*face_vertex_NE, *face_vertex_SW,
                       fill=face_color,
                       width=CUBE_LINE_WIDTH,
                       capstyle=tk.ROUND)

    canvas.create_line(*face_vertex_NW, *face_vertex_SE,
                       fill=face_color,
                       width=CUBE_LINE_WIDTH,
                       capstyle=tk.ROUND)


def draw_mountain_face(canvas, cube_center, cube_vertices, face_color):

    if USE_JERSI_PURE_STYLE:
        draw_pure_mountain_face(canvas, cube_center, cube_vertices, face_color)
    else:
        draw_simple_mountain_face(canvas, cube_center, cube_vertices, face_color)


def draw_pure_mountain_face(canvas, cube_center, cube_vertices, face_color):

    face_vertex_NE = 0.5*cube_center + 0.5*cube_vertices[0]
    face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
    face_vertex_SW = 0.5*cube_center + 0.5*cube_vertices[2]
    face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

    face_N = 0.5*(face_vertex_NW + face_vertex_NE)
    face_S = 0.5*(face_vertex_SW + face_vertex_SE)

    face_W = 0.5*(face_vertex_NW + face_vertex_SW)
    face_E = 0.5*(face_vertex_NE + face_vertex_SE)

    face_data = [*face_N, *face_W, *face_E]

    canvas.create_polygon(face_data,
                          fill='',
                          outline=face_color,
                          width=CUBE_LINE_WIDTH,
                          joinstyle=tk.ROUND)

    face_data = [*face_S, *face_W, *face_E]

    canvas.create_polygon(face_data,
                          fill='',
                          outline=face_color,
                          width=CUBE_LINE_WIDTH,
                          joinstyle=tk.ROUND)

def draw_simple_mountain_face(canvas, cube_center, cube_vertices, face_color):

    face_vertex_NE = 0.5*cube_center + 0.5*cube_vertices[0]
    face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
    face_vertex_SW = 0.5*cube_center + 0.5*cube_vertices[2]
    face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

    face_vertex_N = 0.5*(face_vertex_NW + face_vertex_NE)
    face_vertex_S = 0.5*(face_vertex_SW + face_vertex_SE)

    face_half_width = 0.5*(face_vertex_NE - face_vertex_NW)

    face_center_up = cube_center + CUBE_LINE_WIDTH*UNIT_Y
    face_center_down = cube_center - CUBE_LINE_WIDTH*UNIT_Y

    face_up_W = face_center_up - face_half_width
    face_up_E = face_center_up + face_half_width

    face_down_W = face_center_down - face_half_width
    face_down_E = face_center_down + face_half_width

    face_data = [*face_vertex_N, *face_up_W, *face_up_E]

    canvas.create_polygon(face_data,
                          fill=face_color,
                          outline=face_color,
                          width=CUBE_LINE_WIDTH,
                          joinstyle=tk.MITER)

    face_data = [*face_vertex_S, *face_down_W, *face_down_E]

    canvas.create_polygon(face_data,
                          fill=face_color,
                          outline=face_color,
                          width=CUBE_LINE_WIDTH,
                          joinstyle=tk.MITER)


def draw_wise_face(canvas, cube_center, cube_vertices, face_color):

    draw_lemniscate = True

    face_vertex_NE = 0.5*cube_center + 0.5*cube_vertices[0]
    face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
    face_vertex_SW = 0.5*cube_center + 0.5*cube_vertices[2]
    face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

    face_vertex_W = 0.5*(face_vertex_NW + face_vertex_SW)

    wise_data = list()

    if draw_lemniscate:

        # -- Equation retrieve from my GeoGebra drawings --
        # Curve(x(C) + (x(C) - x(W)) cos(t) / (1 + sin²(t)),
        #        y(C) + (x(C) - x(W)) cos(t) sin(t) / (1 + sin²(t)),
        #        t, 0, 2π)
        # C : cube_center
        # W : face_vertex_W

        delta = cube_center[0] - face_vertex_W[0]

        angle_count = 20
        for angle_index in range(angle_count):
            angle_value = angle_index*2*math.pi/angle_count

            angle_sinus = math.sin(angle_value)
            angle_cosinus = math.cos(angle_value)

            x = cube_center[0] + delta*angle_cosinus/(1 + angle_sinus**2)
            y = cube_center[1] + delta*angle_cosinus*angle_sinus/(1 + angle_sinus**2)

            wise_data.append(x)
            wise_data.append(y)

    else:
        wise_data.extend(face_vertex_NW)
        wise_data.extend(face_vertex_SE)
        wise_data.extend(face_vertex_NE)
        wise_data.extend(face_vertex_SW)

    canvas.create_polygon(wise_data,
                          fill='',
                          outline=face_color,
                          width=CUBE_LINE_WIDTH,
                          joinstyle=tk.ROUND,
                          smooth=True)


FACE_DRAWERS = dict()
FACE_DRAWERS[CubeType.FOOL] = draw_fool_face
FACE_DRAWERS[CubeType.KING] = draw_king_face
FACE_DRAWERS[CubeType.PAPER] = draw_paper_face
FACE_DRAWERS[CubeType.ROCK] = draw_rock_face
FACE_DRAWERS[CubeType.SCISSORS] = draw_scissors_face
FACE_DRAWERS[CubeType.MOUNTAIN] = draw_mountain_face
FACE_DRAWERS[CubeType.WISE] = draw_wise_face


def draw_all_hexagons(canvas):

    for (_, hexagon) in Hexagon.alls.items():
        draw_hexagon(canvas,
                     position_uv=hexagon.position_uv,
                     fill_color=hexagon.color,
                     label=hexagon.label,
                     is_extra=hexagon.is_extra,
                     extra_shift=hexagon.extra_shift)


def draw_hexagon(canvas, position_uv, fill_color='', line_color='black',
                 label='', is_extra=False, extra_shift=None):

    if is_extra and not DRAW_EXTRA:
        return

    (u, v) = position_uv

    hexagon_center = ORIGIN + HEXA_WIDTH*(u*UNIT_U + v*UNIT_V)

    if extra_shift is not None:
        hexagon_center = hexagon_center + extra_shift

    hexagon_data = list()

    for vertex_index in range(HEXA_VERTEX_COUNT):
        vertex_angle = (1/2 + vertex_index)*HEXA_SIDE_ANGLE

        hexagon_vertex = hexagon_center
        hexagon_vertex = hexagon_vertex + HEXA_SIDE*math.cos(vertex_angle)*UNIT_X
        hexagon_vertex = hexagon_vertex + HEXA_SIDE*math.sin(vertex_angle)*UNIT_Y

        hexagon_data.append(hexagon_vertex[0])
        hexagon_data.append(hexagon_vertex[1])

        if vertex_index == 3:
            label_position = hexagon_vertex + 0.25*HEXA_SIDE*(UNIT_X + 0.75*UNIT_Y)


    if is_extra:
        polygon_line_color = ''
    else:
        polygon_line_color = line_color

    canvas.create_polygon(hexagon_data,
                          fill=fill_color,
                          outline=polygon_line_color,
                          width=HEXA_LINE_WIDTH,
                          joinstyle=tk.MITER)

    if label and not is_extra:
        label_font = font.Font(family=FONT_FAMILY, size=FONT_LABEL_SIZE, weight='bold')

        canvas.create_text(*label_position, text=label, justify=tk.CENTER, font=label_font)


def draw_cube(canvas, key, config, color, cube_type=None):

    hexagon = Hexagon.alls[key]

    if hexagon.is_extra and not DRAW_EXTRA:
        return

    (u, v) = hexagon.position_uv

    hexagon_center = ORIGIN + HEXA_WIDTH*(u*UNIT_U + v*UNIT_V)

    if hexagon.extra_shift is not None:
        hexagon_center = hexagon_center + hexagon.extra_shift

    cube_vertices = list()

    for vertex_index in range(CUBE_VERTEX_COUNT):
        vertex_angle = (1/2 + vertex_index)*CUBE_SIDE_ANGLE

        if config == CubeConfig.SINGLE:
            cube_center = hexagon_center

        elif config == CubeConfig.BOTTOM:
            cube_center = hexagon_center - 0.40*HEXA_SIDE*UNIT_Y

        elif config == CubeConfig.TOP:
            cube_center = hexagon_center + 0.40*HEXA_SIDE*UNIT_Y

        cube_vertex = cube_center
        cube_vertex = cube_vertex + 0.5*HEXA_SIDE*math.cos(vertex_angle)*UNIT_X
        cube_vertex = cube_vertex + 0.5*HEXA_SIDE*math.sin(vertex_angle)*UNIT_Y

        cube_vertices.append(cube_vertex)


    if color == CubeColor.BLACK:
        fill_color = 'black'
        face_color = 'white'
        str_transformation = str.lower

    elif color == CubeColor.WHITE:
        fill_color = 'white'
        face_color = 'black'
        str_transformation = str.upper

    else:
        jersi_assert(False, "not a CubeColor '%s'" % color)


    line_color = ''

    cube_vertex_NW = cube_vertices[1]
    cube_vertex_SE = cube_vertices[3]

    canvas.create_rectangle(*cube_vertex_NW, *cube_vertex_SE,
                            fill=fill_color,
                            outline=line_color)

    if cube_type is not None:

        if DRAW_CUBE_FACES:
            FACE_DRAWERS[cube_type](canvas, cube_center, cube_vertices, face_color)

        else:
            face_font = font.Font(family=FONT_FAMILY, size=FONT_FACE_SIZE, weight='bold')

            canvas.create_text(*cube_center,
                               text=str_transformation(cube_type.value),
                               justify=tk.CENTER,
                               font=face_font,
                               fill=face_color)


def draw_state(canvas):

    canvas.delete('all')

    draw_all_hexagons(canvas)

    for (position_label, position_state) in STATE.items():

        if position_state[1] is not None:

            (cube_type, cube_color) = position_state[1]
            draw_cube(canvas, key=position_label, config=CubeConfig.TOP,
                      color=cube_color, cube_type=cube_type)

            (cube_type, cube_color) = position_state[0]
            draw_cube(canvas, key=position_label, config=CubeConfig.BOTTOM,
                      color=cube_color, cube_type=cube_type)

        elif position_state[0] is not None:

            (cube_type, cube_color) = position_state[0]
            draw_cube(canvas, key=position_label, config=CubeConfig.SINGLE,
                      color=cube_color, cube_type=cube_type)

        else:
            pass


def draw_jersi():

    main_window =tk.Tk()

    tk.Tk.iconbitmap(main_window, default=JERSI_ICON_FILE)
    tk.Tk.wm_title(main_window, "jersi drawer tk : draw a vectorial picture from an abstract state")

    main_canvas = tk.Canvas(main_window,
                            height=CANVAS_HEIGHT,
                            width=CANVAS_WIDTH)

    dir_name_variable = tk.StringVar()
    dir_name_label = tk.Label(main_window,
                               textvariable=dir_name_variable,
                               width=90)

    file_name_variable = tk.StringVar()
    file_name_label = tk.Label(main_window,
                               textvariable=file_name_variable,
                               width=90)

    log_variable = tk.StringVar()
    log_label = tk.Label(main_window,
                               textvariable=log_variable,
                               width=90,
                               foreground='red')

    face_value = tk.BooleanVar()
    face_value.set(DRAW_CUBE_FACES)
    face_check_button = ttk.Checkbutton (main_window,
                                   text='Icon faces',
                                   command=lambda:toggle_face(main_canvas,
                                                              face_value.get(),
                                                              log_variable),
                                   variable=face_value)

    extra_value = tk.BooleanVar()
    extra_value.set(DRAW_EXTRA)
    extra_check_button = ttk.Checkbutton (main_window,
                                   text='Reserve',
                                   command=lambda:toggle_extra(main_canvas,
                                                               extra_value.get(),
                                                               log_variable),
                                   variable=extra_value)

    quit_button = ttk.Button(main_window,
                             text='Quit',
                             command=main_window.destroy)

    read_button = ttk.Button(main_window,
                              text='Read',
                              command=lambda:read_selected_file(main_canvas,
                                                       dir_name_variable,
                                                       file_name_variable,
                                                       log_variable))

    write_button = ttk.Button(main_window,
                              text='Write',
                              command=lambda:write_file(main_canvas,
                                                        log_variable))

    read_button.grid(row=0, column=0, sticky=tk.W)
    write_button.grid(row=0, column=1, sticky=tk.W)
    face_check_button.grid(row=0, column=2)
    extra_check_button.grid(row=0, column=3)
    quit_button.grid(row=0, column=4, sticky=tk.E)

    dir_name_label.grid(row=1, columnspan=5)
    file_name_label.grid(row=2, columnspan=5)
    log_label.grid(row=3, columnspan=5)

    main_canvas.grid(row=4, columnspan=5)

    if True:
        init_state()
        draw_state(main_canvas)

    else:
        # Load and redraw from the default import state file
        dir_name_variable.set(os.path.dirname(JERSI_STATE_FILE))
        file_name_variable.set(os.path.basename(JERSI_STATE_FILE))
        read_file(main_canvas, log_variable)

    main_window.mainloop()


def toggle_face(canvas, draw_cube_faces, log_variable):

    log_variable.set("toggle face ...")

    global DRAW_CUBE_FACES
    DRAW_CUBE_FACES = draw_cube_faces
    draw_state(canvas)

    log_variable.set("toggle face done")


def toggle_extra(canvas, draw_extra, log_variable):

    log_variable.set("toggle reserve ...")

    global DRAW_EXTRA
    DRAW_EXTRA = draw_extra
    draw_state(canvas)

    log_variable.set("toggle reserve done")


def read_selected_file(canvas, dir_name_variable, file_name_variable, log_variable):

    file_name = filedialog.askopenfilename(initialdir=os.path.join(JERSI_HOME, "states", "import"),
                                                title="Select file",
                                                filetypes=(("text files","*.txt"),("all files","*.*")))

    dir_name_variable.set(os.path.dirname(file_name))
    file_name_variable.set(os.path.basename(file_name))

    global JERSI_STATE_FILE
    JERSI_STATE_FILE = file_name

    read_file(canvas, log_variable)


def read_file(canvas, log_variable):


    log_variable.set("Reading ...")

    try:
        read_state_file(JERSI_STATE_FILE)
        draw_state(canvas)
        log_variable.set("Read done")

    except(JersiError) as jersi_assertion_error:
        log_variable.set("Read failed: %s !!!" % jersi_assertion_error.message)

    except:
        log_variable.set("Read failed !!!")


def write_file(canvas, log_variable):

    log_variable.set("Writing ...")

    try:
        write_ps_file = False
        write_png_file = False
        write_pdf_file = True
        write_emf_file = True

        state_import_name = os.path.basename(JERSI_STATE_FILE)

        (state_import_radix, state_import_extension) = os.path.splitext(state_import_name)
        jersi_assert(state_import_extension == ".txt",
                     "unexpected extension for import file '%s'" % state_import_name)

        state_import_dir = os.path.dirname(JERSI_STATE_FILE)
        state_import_updir = os.path.dirname(state_import_dir)

        state_import_subdir = os.path.basename(state_import_dir)
        jersi_assert(state_import_subdir == "import",
                     "unexpected import subdir '%s'" % state_import_subdir)

        state_export_radix = state_import_radix
        state_export_subdir = "export"
        state_export_updir = state_import_updir
        state_export_path = os.path.join(state_export_updir, state_export_subdir, state_export_radix)

        state_ps_file = state_export_path + '.ps'
        state_pdf_file = state_export_path + '.pdf'
        state_png_file = state_export_path + '.png'
        state_emf_file = state_export_path + '.emf'

        canvas_is_landscape = (CANVAS_WIDTH > CANVAS_HEIGHT)

        canvas.postscript(file=state_ps_file,
                          colormode='color',
                          rotate=canvas_is_landscape)

        if write_png_file:
            PIL.Image.open(state_ps_file).save(state_png_file)

        if write_pdf_file:
            subprocess.run(["inkscape",
                                    "--export-pdf=" + state_pdf_file,
                                    "--file=" + state_ps_file])

        if write_emf_file:
            subprocess.run(["inkscape",
                                    "--export-emf=" + state_emf_file,
                                    "--file=" + state_ps_file])

        if not write_ps_file:
            os.remove(state_ps_file)

        log_variable.set("Write done")

    except(JersiError) as jersi_assertion_error:
        log_variable.set("Write failed: %s !!!" % jersi_assertion_error.message)

    except:
        log_variable.set("Write failed !!!")



def reset_state():
    for (_, hexagon) in Hexagon.alls.items():
        STATE[hexagon.label] = [None, None]


def init_state():
    reset_state()

    # whites
    set_cube_at_position('b1', 'F')
    set_cube_at_position('b8', 'F')
    set_cube_at_position('a4', 'K')

    set_cube_at_position('b2', 'R')
    set_cube_at_position('b3', 'P')
    set_cube_at_position('b4', 'S')
    set_cube_at_position('b5', 'R')
    set_cube_at_position('b6', 'P')
    set_cube_at_position('b7', 'S')

    set_cube_at_position('a3', 'R')
    set_cube_at_position('a2', 'S')
    set_cube_at_position('a1', 'P')
    set_cube_at_position('a5', 'S')
    set_cube_at_position('a6', 'R')
    set_cube_at_position('a7', 'P')

    # blacks
    set_cube_at_position('h1', 'f')
    set_cube_at_position('h8', 'f')
    set_cube_at_position('i4', 'k')

    set_cube_at_position('h7', 'r')
    set_cube_at_position('h6', 'p')
    set_cube_at_position('h5', 's')
    set_cube_at_position('h4', 'r')
    set_cube_at_position('h3', 'p')
    set_cube_at_position('h2', 's')

    set_cube_at_position('i5', 'r')
    set_cube_at_position('i6', 's')
    set_cube_at_position('i7', 'p')
    set_cube_at_position('i3', 's')
    set_cube_at_position('i2', 'r')
    set_cube_at_position('i1', 'p')

    # white reserve
    set_cube_at_position('c', 'W')
    set_cube_at_position('c', 'W')

    set_cube_at_position('b', 'M')
    set_cube_at_position('b', 'M')

    set_cube_at_position('a', 'M')
    set_cube_at_position('a', 'M')

    # black reserve
    set_cube_at_position('i', 'm')
    set_cube_at_position('i', 'm')

    set_cube_at_position('h', 'm')
    set_cube_at_position('h', 'm')

    set_cube_at_position('g', 'w')
    set_cube_at_position('g', 'w')


def read_state_file(file_name):
    global STATE
    reset_state()

    instructions = list()

    file_is_valid = True

    with open(file_name, 'r') as file_stream:
        for line in file_stream:

            if re.match(r'^\s*$', line):
                pass

            elif re.match(r'^\s*#.*$', line):
                pass

            else:
                line = re.sub(r'\s', '', line)

                for item in re.split(r'/', line):
                    if re.match(r'^([KFRPSMW]|[kfrpsmw]):[a-i][1-9]?$', item):
                        instructions.append(re.split(r':', item))
                    else:
                        file_is_valid = False
                        raise JersiError(r"wrong item '%s' in line '%s'" % (item, line))

    if file_is_valid:
        for (cube_label, position_label) in instructions:
            set_cube_at_position(position_label, cube_label)


def set_cube_at_position(position_label, cube_label):

    jersi_assert(position_label in Hexagon.alls,
                 "no hexagon at label '%s'" % position_label)


    jersi_assert(position_label in Hexagon.alls,
                 "no cube colored type '%s'" % cube_label)

    if STATE[position_label][0] is None:
        STATE[position_label][0] = CUBE_COLORED_TYPES[cube_label]

    elif STATE[position_label][1] is None:
        STATE[position_label][1] = CUBE_COLORED_TYPES[cube_label]

    else:
        raise("No room for cube '%s' at position '%s' !!!" % (cube_label, position_label))


def main():
    print("Hello")

    print(_COPYRIGHT_AND_LICENSE)

    draw_jersi()

    print("Bye")


if __name__ == "__main__":
    main()