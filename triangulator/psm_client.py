"""Client pour récupérer les PointSet auprès du PointSetManager."""

import os

PSM_URL = os.environ.get("PSM_URL", "http://localhost:5001")
TIMEOUT = 5


class PointSetNotFoundError(Exception):
    """PointSet introuvable (404)."""


class PointSetManagerError(Exception):
    """PointSetManager en panne ou injoignable."""


def get_pointset(pointset_id: str) -> bytes:
    """Récupère le binaire du PointSet auprès du PointSetManager."""
    raise NotImplementedError
