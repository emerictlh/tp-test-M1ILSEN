"""Tests de performance (PLAN section 4), lancer avec make perf_test."""

import random
import time
from unittest.mock import patch

import pytest

from triangulator.app import app
from triangulator.binary import (
    decode_pointset,
    decode_triangles,
    encode_pointset,
    encode_triangles,
)
from triangulator.triangulation import triangulate


def random_points(n, seed=0):
    """N points aléatoires (graine fixe)."""
    rng = random.Random(seed)
    return [(rng.uniform(0, 1000), rng.uniform(0, 1000)) for _ in range(n)]


def timed(func, *args):
    """Renvoie (résultat, durée en secondes)."""
    start = time.perf_counter()
    result = func(*args)
    return result, time.perf_counter() - start


# 4.1
@pytest.mark.performance
@pytest.mark.parametrize(("n", "budget"), [(100, 0.1), (1000, 0.5), (10000, 5.0)])
def test_triangulation_time(n, budget):
    """La triangulation reste sous le budget."""
    _, duration = timed(triangulate, random_points(n))
    print(f"{n} points : {duration:.3f}s")
    assert duration < budget


# 4.2
@pytest.mark.performance
def test_triangulation_scaling():
    """Doubler n ne doit pas plus que quadrupler le temps."""
    _, t1 = timed(triangulate, random_points(5000))
    _, t2 = timed(triangulate, random_points(10000))
    assert t2 / t1 < 4


# 4.3
@pytest.mark.performance
def test_pointset_encode_decode_time():
    """Encodage / décodage de 100 000 points."""
    points = random_points(100_000)
    data, t_enc = timed(encode_pointset, points)
    _, t_dec = timed(decode_pointset, data)
    assert t_enc < 2.0
    assert t_dec < 2.0


@pytest.mark.performance
def test_triangles_encode_decode_time():
    """Encodage / décodage des Triangles de 10 000 points."""
    points = random_points(10000)
    triangles = triangulate(points)
    data, t_enc = timed(encode_triangles, points, triangles)
    _, t_dec = timed(decode_triangles, data)
    assert t_enc < 2.0
    assert t_dec < 2.0


# 4.4
@pytest.mark.performance
def test_api_response_time():
    """Requête complète sur 10 000 points."""
    data = encode_pointset(random_points(10000))
    client = app.test_client()
    with patch("triangulator.psm_client.get_pointset", return_value=data):
        resp, duration = timed(
            client.get, "/triangulation/123e4567-e89b-12d3-a456-426614174000"
        )
    assert resp.status_code == 200
    assert duration < 5.0
