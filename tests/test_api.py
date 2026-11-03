"""Tests de l'API (PLAN section 3), le PointSetManager est mocké."""

from unittest.mock import patch

import pytest

from triangulator import psm_client
from triangulator.app import app
from triangulator.binary import decode_triangles, encode_pointset

VALID_ID = "123e4567-e89b-12d3-a456-426614174000"
SQUARE = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]


@pytest.fixture
def client():
    """Client de test Flask."""
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def psm():
    """Mock de psm_client.get_pointset, renvoie un carré par défaut."""
    with patch("triangulator.psm_client.get_pointset") as mock:
        mock.return_value = encode_pointset(SQUARE)
        yield mock


# 3.1 happy path
def test_triangulation_ok(client, psm):
    """Cas normal : 200 + binaire Triangles valide."""
    resp = client.get(f"/triangulation/{VALID_ID}")
    assert resp.status_code == 200
    assert resp.mimetype == "application/octet-stream"
    points, triangles = decode_triangles(resp.data)
    assert points == SQUARE
    assert len(triangles) == 2


# 3.2 bon id transmis
def test_psm_called_with_id(client, psm):
    """Le PSM est appelé une fois avec le bon id."""
    client.get(f"/triangulation/{VALID_ID}")
    psm.assert_called_once_with(VALID_ID)


# 3.3 id mal formé
@pytest.mark.parametrize(
    "bad_id",
    [
        "abc",
        "123",
        "123e4567-e89b-12d3-a456",
        "123e4567e89b12d3a456426614174000",
    ],
)
def test_invalid_id(client, psm, bad_id):
    """Un id qui n'est pas un UUID donne 400."""
    resp = client.get(f"/triangulation/{bad_id}")
    assert resp.status_code == 400
    assert resp.json["code"] == "INVALID_ID"
    psm.assert_not_called()


# 3.4 id inconnu
def test_unknown_id(client, psm):
    """Le PSM répond 404 -> on renvoie 404."""
    psm.side_effect = psm_client.PointSetNotFoundError(VALID_ID)
    resp = client.get(f"/triangulation/{VALID_ID}")
    assert resp.status_code == 404
    assert resp.json["code"] == "NOT_FOUND"


# 3.5 PSM en panne
def test_psm_unavailable(client, psm):
    """PSM injoignable -> 503."""
    psm.side_effect = psm_client.PointSetManagerError("down")
    resp = client.get(f"/triangulation/{VALID_ID}")
    assert resp.status_code == 503
    assert "message" in resp.json


# 3.6 données corrompues
def test_corrupted_pointset(client, psm):
    """Binaire invalide -> 500."""
    psm.return_value = b"\x05\x00"
    resp = client.get(f"/triangulation/{VALID_ID}")
    assert resp.status_code == 500


# 3.7 triangulation impossible
@pytest.mark.parametrize(
    "points",
    [[(0.0, 0.0), (1.0, 1.0)], [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]],
    ids=["2_points", "alignes"],
)
def test_triangulation_failed(client, psm, points):
    """Triangulation impossible -> erreur JSON TRIANGULATION_FAILED."""
    psm.return_value = encode_pointset(points)
    resp = client.get(f"/triangulation/{VALID_ID}")
    assert resp.status_code == 500
    assert resp.json["code"] == "TRIANGULATION_FAILED"


# 3.8 autres routes / méthodes
def test_post_not_allowed(client, psm):
    """POST -> 405."""
    resp = client.post(f"/triangulation/{VALID_ID}")
    assert resp.status_code == 405
    psm.assert_not_called()


def test_unknown_route(client, psm):
    """Route inconnue -> 404."""
    resp = client.get("/pointset")
    assert resp.status_code == 404
    psm.assert_not_called()
