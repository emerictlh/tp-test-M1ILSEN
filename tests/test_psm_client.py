"""Tests du client PointSetManager (urlopen mocké)."""

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from triangulator import psm_client

ID = "123e4567-e89b-12d3-a456-426614174000"


@patch("urllib.request.urlopen")
def test_get_pointset_ok(urlopen):
    """Renvoie le contenu de la réponse."""
    resp = MagicMock()
    resp.__enter__.return_value.read.return_value = b"data"
    urlopen.return_value = resp
    assert psm_client.get_pointset(ID) == b"data"


@patch("urllib.request.urlopen")
def test_not_found(urlopen):
    """404 -> PointSetNotFoundError."""
    urlopen.side_effect = urllib.error.HTTPError("url", 404, "err", None, None)
    with pytest.raises(psm_client.PointSetNotFoundError):
        psm_client.get_pointset(ID)


@patch("urllib.request.urlopen")
def test_psm_down(urlopen):
    """Connexion impossible -> PointSetManagerError."""
    urlopen.side_effect = urllib.error.URLError("connection refused")
    with pytest.raises(psm_client.PointSetManagerError):
        psm_client.get_pointset(ID)
