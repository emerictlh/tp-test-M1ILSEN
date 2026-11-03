"""Encodage et décodage binaire des PointSet et Triangles."""

from triangulator.triangulation import Point, Triangle


class BinaryFormatError(ValueError):
    """Erreur quand le binaire est mal formé."""


def encode_pointset(points: list[Point]) -> bytes:
    """Encode des points en binaire PointSet."""
    raise NotImplementedError


def decode_pointset(data: bytes) -> list[Point]:
    """Décode un binaire PointSet (BinaryFormatError si invalide)."""
    raise NotImplementedError


def encode_triangles(points: list[Point], triangles: list[Triangle]) -> bytes:
    """Encode les points et les triangles en binaire Triangles."""
    raise NotImplementedError


def decode_triangles(data: bytes) -> tuple[list[Point], list[Triangle]]:
    """Décode un binaire Triangles (BinaryFormatError si invalide)."""
    raise NotImplementedError
