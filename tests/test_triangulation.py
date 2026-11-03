"""Tests de la triangulation (PLAN section 1)."""

import random

import pytest

from triangulator.triangulation import TriangulationError, triangulate

# jeux de points : (points, aire de l'enveloppe, nb de points sur le contour)
TRIANGLE = ([(0.0, 0.0), (4.0, 0.0), (0.0, 4.0)], 8.0, 3)
SQUARE = ([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)], 4.0, 4)
TRIANGLE_WITH_CENTER = ([(0.0, 0.0), (4.0, 0.0), (0.0, 4.0), (1.0, 1.0)], 8.0, 3)
PENTAGON = ([(0.0, 0.0), (4.0, 0.0), (5.0, 3.0), (2.0, 5.0), (-1.0, 3.0)], 21.0, 5)
SQUARE_WITH_INNER = (
    [
        (0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0),
        (3.0, 4.0), (6.0, 2.0), (7.0, 6.0), (2.0, 7.0),
    ],
    100.0,
    4,
)

DATASETS = {
    "triangle": TRIANGLE,
    "square": SQUARE,
    "triangle_with_center": TRIANGLE_WITH_CENTER,
    "pentagon": PENTAGON,
    "square_with_inner": SQUARE_WITH_INNER,
}


def triangle_area(points, triangle):
    """Aire d'un triangle à partir de ses indices."""
    ax, ay = points[triangle[0]]
    bx, by = points[triangle[1]]
    cx, cy = points[triangle[2]]
    return abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay)) / 2


def total_area(points, triangles):
    """Somme des aires des triangles."""
    total = 0
    for t in triangles:
        total += triangle_area(points, t)
    return total


def check_triangles(points, triangles):
    """Vérifie que les triangles sont valides."""
    for t in triangles:
        assert len(t) == 3
        for i in t:
            assert 0 <= i < len(points)
        assert t[0] != t[1] and t[1] != t[2] and t[0] != t[2]
        assert triangle_area(points, t) > 0
    # pas de doublon
    assert len(set(triangles)) == len(triangles)


# 1.1 tous les points utilisés
@pytest.mark.parametrize("name", DATASETS)
def test_all_points_are_used(name):
    """Chaque point est dans au moins un triangle."""
    points, _, _ = DATASETS[name]
    triangles = triangulate(points)
    used = []
    for t in triangles:
        for i in t:
            if i not in used:
                used.append(i)
    assert sorted(used) == list(range(len(points)))


# 1.2 points alignés
@pytest.mark.parametrize(
    "points",
    [
        [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)],
        [(0.0, 0.0), (0.0, 1.0), (0.0, 2.0)],
        [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (5.0, 5.0)],
    ],
)
def test_collinear_points_raise(points):
    """Points alignés -> erreur."""
    with pytest.raises(TriangulationError):
        triangulate(points)


# 1.3 pas assez de points
@pytest.mark.parametrize("points", [[], [(0.0, 0.0)], [(0.0, 0.0), (1.0, 1.0)]])
def test_not_enough_points_raise(points):
    """Moins de 3 points -> erreur."""
    with pytest.raises(TriangulationError):
        triangulate(points)


# 1.4 cas simples
def test_one_triangle():
    """3 points -> 1 triangle."""
    points, _, _ = TRIANGLE
    triangles = triangulate(points)
    assert len(triangles) == 1
    assert sorted(triangles[0]) == [0, 1, 2]


def test_square():
    """Carré -> 2 triangles."""
    points, _, _ = SQUARE
    triangles = triangulate(points)
    assert len(triangles) == 2
    check_triangles(points, triangles)


def test_triangle_with_center():
    """Triangle + point au milieu -> 3 triangles."""
    points, _, _ = TRIANGLE_WITH_CENTER
    triangles = triangulate(points)
    assert len(triangles) == 3
    check_triangles(points, triangles)


# 1.5 pas de superposition
@pytest.mark.parametrize("name", DATASETS)
def test_total_area(name):
    """Somme des aires = aire de l'enveloppe convexe."""
    points, area, _ = DATASETS[name]
    triangles = triangulate(points)
    assert total_area(points, triangles) == pytest.approx(area)


# 1.6 nombre de triangles = 2n - h - 2
@pytest.mark.parametrize("name", DATASETS)
def test_triangle_count(name):
    """Formule 2n - h - 2."""
    points, _, h = DATASETS[name]
    triangles = triangulate(points)
    assert len(triangles) == 2 * len(points) - h - 2


# 1.7 triangles valides
@pytest.mark.parametrize("name", DATASETS)
def test_triangles_are_valid(name):
    """Chaque triangle est valide."""
    points, _, _ = DATASETS[name]
    check_triangles(points, triangulate(points))


# 1.8 coordonnées négatives, décimales, grandes
@pytest.mark.parametrize(
    ("points", "area"),
    [
        (
            [
                (-50.0, -30.0), (-40.0, -30.0), (-40.0, -20.0), (-50.0, -20.0),
                (-47.0, -26.0), (-44.0, -28.0), (-43.0, -24.0), (-48.0, -23.0),
            ],
            100.0,
        ),
        (
            [
                (0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0),
                (0.3, 0.4), (0.6, 0.2), (0.7, 0.6), (0.2, 0.7),
            ],
            1.0,
        ),
        (
            [
                (0.0, 0.0), (1e7, 0.0), (1e7, 1e7), (0.0, 1e7),
                (3e6, 4e6), (6e6, 2e6), (7e6, 6e6), (2e6, 7e6),
            ],
            1e14,
        ),
    ],
)
def test_other_coordinates(points, area):
    """Ça marche aussi avec d'autres coordonnées."""
    triangles = triangulate(points)
    check_triangles(points, triangles)
    assert len(triangles) == 2 * 8 - 4 - 2
    assert total_area(points, triangles) == pytest.approx(area)


# 1.9 doublons
def test_duplicate_point():
    """Un point en double est ignoré."""
    points, area, _ = SQUARE_WITH_INNER
    points = points + [(3.0, 4.0)]
    triangles = triangulate(points)
    check_triangles(points, triangles)
    assert len(triangles) == 10
    assert total_area(points, triangles) == pytest.approx(area)


# 1.10 ordre des points
@pytest.mark.parametrize("seed", [0, 1, 42])
def test_point_order(seed):
    """Mélanger les points ne change pas le résultat."""
    points, _, _ = SQUARE_WITH_INNER
    shuffled = list(points)
    random.Random(seed).shuffle(shuffled)
    t1 = triangulate(points)
    t2 = triangulate(shuffled)
    assert len(t1) == len(t2)
    assert total_area(points, t1) == pytest.approx(total_area(shuffled, t2))
