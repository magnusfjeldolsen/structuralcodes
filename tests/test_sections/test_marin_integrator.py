"""Tests for the Marin section integrator."""

from shapely import Polygon
from shapely.testing import assert_geometries_equal

from structuralcodes.geometry import (
    SurfaceGeometry,
    add_reinforcement_line,
)
from structuralcodes.materials.concrete import ConcreteMC2010
from structuralcodes.materials.reinforcement import ReinforcementMC2010
from structuralcodes.sections.section_integrators import MarinIntegrator


def _reinforced_geometry():
    """A simple rectangular RC section with a line of four bars."""
    concrete = ConcreteMC2010(25)
    steel = ReinforcementMC2010(fyk=450, Es=210000, ftk=450, epsuk=0.03)
    geo = SurfaceGeometry(
        Polygon(((0, 0), (200, 0), (200, 400), (0, 400))), concrete
    )
    return add_reinforcement_line(geo, (40, 40), (160, 40), 20, steel, n=4)


def test_marin_integrator_caches_rotated_geometry():
    """The rotated geometry is memoized per (geometry, angle).

    The rotation applied before Marin integration depends only on the curvature
    direction, so within a calculation the same angle is requested many times.
    Caching must return the same object for a repeated angle, recompute for a
    different angle, match an explicit ``rotate()``, and reset when a different
    geometry is analysed.
    """
    integrator = MarinIntegrator()
    geo = _reinforced_geometry()

    # Same angle -> same cached object (no recompute).
    r1 = integrator._rotated_geometry(geo, 0.3)
    r2 = integrator._rotated_geometry(geo, 0.3)
    assert r2 is r1

    # The cached geometry matches an explicit rotate().
    assert_geometries_equal(
        r1.geometries[0].polygon, geo.rotate(0.3).geometries[0].polygon
    )

    # A different angle recomputes.
    r3 = integrator._rotated_geometry(geo, -0.5)
    assert r3 is not r1

    # Analysing a different geometry resets the cache.
    r4 = integrator._rotated_geometry(geo.translate(10.0, 0.0), 0.3)
    assert r4 is not r1


def test_marin_integrator_cache_toggle_off():
    """With caching disabled every call returns a freshly rotated geometry."""
    integrator = MarinIntegrator()
    integrator.cache_rotations = False
    geo = _reinforced_geometry()

    r1 = integrator._rotated_geometry(geo, 0.3)
    r2 = integrator._rotated_geometry(geo, 0.3)
    assert r2 is not r1
    assert_geometries_equal(r1.geometries[0].polygon, r2.geometries[0].polygon)
