"""Triangulation d'un ensemble de points 2D."""

Point = tuple[float, float]
Triangle = tuple[int, int, int]


class TriangulationError(Exception):
    """Erreur quand on ne peut pas trianguler (moins de 3 points, alignés...)."""


def triangulate(points: list[Point]) -> list[Triangle]:
    """Renvoie les triangles (indices des points). Les doublons sont ignorés."""
    raise NotImplementedError
