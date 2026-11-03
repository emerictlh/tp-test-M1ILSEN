"""Tests de l'encodage / décodage binaire (PLAN section 2)."""

import struct

import pytest

from triangulator.binary import (
    BinaryFormatError,
    decode_pointset,
    decode_triangles,
    encode_pointset,
    encode_triangles,
)

SQUARE = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
# le même carré en binaire, fait à la main
SQUARE_BIN = struct.pack("<I", 4) + struct.pack("<8f", 0, 0, 2, 0, 2, 2, 0, 2)


# 2.1 round-trip
def test_pointset_round_trip():
    """Encoder puis décoder redonne les mêmes points."""
    assert decode_pointset(encode_pointset(SQUARE)) == SQUARE


# 2.2 binaire fait à la main
def test_decode_handmade_binary():
    """Décodage d'un binaire construit avec struct."""
    data = struct.pack("<I", 2) + struct.pack("<ff", 1.5, -3.0)
    data += struct.pack("<ff", 4.0, 8.25)
    assert decode_pointset(data) == [(1.5, -3.0), (4.0, 8.25)]


def test_encode_matches_handmade_binary():
    """L'encodage donne le même binaire que celui fait à la main."""
    expected = struct.pack("<I", 2) + struct.pack("<ff", 1.5, -3.0)
    expected += struct.pack("<ff", 4.0, 8.25)
    assert encode_pointset([(1.5, -3.0), (4.0, 8.25)]) == expected


def test_x_before_y():
    """X est bien écrit avant Y."""
    data = encode_pointset([(1.0, 2.0)])
    assert struct.unpack("<f", data[4:8])[0] == 1.0
    assert struct.unpack("<f", data[8:12])[0] == 2.0


# 2.3 taille
@pytest.mark.parametrize("n", [0, 1, 10])
def test_pointset_size(n):
    """Un PointSet de n points fait 4 + 8n bytes."""
    points = [(float(i), float(i)) for i in range(n)]
    assert len(encode_pointset(points)) == 4 + 8 * n


def test_triangles_size():
    """Taille de Triangles : 4 + 8N + 4 + 12T."""
    data = encode_triangles(SQUARE, [(0, 1, 2), (0, 2, 3)])
    assert len(data) == 4 + 8 * 4 + 4 + 12 * 2


# 2.4 PointSet vide
def test_empty_pointset():
    """PointSet vide = juste le compteur à 0."""
    assert encode_pointset([]) == b"\x00\x00\x00\x00"
    assert decode_pointset(b"\x00\x00\x00\x00") == []


# 2.5 binaires invalides
@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"\x01\x00",
        struct.pack("<I", 3) + struct.pack("<ff", 1.0, 1.0),
        SQUARE_BIN + b"\x00",
    ],
    ids=["vide", "trop_court", "tronque", "bytes_en_trop"],
)
def test_invalid_pointset_raises(data):
    """Un binaire mal formé lève BinaryFormatError."""
    with pytest.raises(BinaryFormatError):
        decode_pointset(data)


@pytest.mark.parametrize(
    "data",
    [
        SQUARE_BIN,
        SQUARE_BIN + struct.pack("<I", 2) + b"\x00" * 12,
        SQUARE_BIN + struct.pack("<IIII", 1, 0, 1, 2) + b"\x00",
    ],
    ids=["sans_compteur", "tronque", "bytes_en_trop"],
)
def test_invalid_triangles_raises(data):
    """Pareil pour Triangles."""
    with pytest.raises(BinaryFormatError):
        decode_triangles(data)


# 2.6 précision des floats
def test_float_precision_exact_values():
    """0.5 et -2.25 sont exacts en float 32 bits."""
    points = [(0.5, -2.25)]
    assert decode_pointset(encode_pointset(points)) == points


def test_float_precision_approx_values():
    """0.1 et 1/3 ne sont pas exacts en float 32 bits."""
    points = [(0.1, 1 / 3)]
    assert decode_pointset(encode_pointset(points)) == points


# 2.7 Triangles
def test_encode_triangles_matches_handmade_binary():
    """Encodage de 4 point + 2 triangles."""
    triangles = [(0, 1, 2), (0, 2, 3)]
    expected = SQUARE_BIN + struct.pack("<I", 2)
    expected += struct.pack("<III", 0, 1, 2) + struct.pack("<III", 0, 2, 3)
    assert encode_triangles(SQUARE, triangles) == expected


def test_triangles_round_trip():
    """Round-trip sur Triangles."""
    triangles = [(0, 1, 2), (0, 2, 3)]
    points, tris = decode_triangles(encode_triangles(SQUARE, triangles))
    assert points == SQUARE
    assert tris == triangles
