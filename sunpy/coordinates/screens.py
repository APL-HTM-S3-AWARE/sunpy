"""
Screen class definitions for making assumptions about off-disk emission
"""
import numpy as np

from astropy.coordinates.representation import CartesianRepresentation, UnitSphericalRepresentation

from sunpy.coordinates import HeliographicStonyhurst

__all__ = ['SphericalScreen', 'PlanarScreen']


class BaseScreen:

    def __init__(self, type, only_off_disk=False):
        self.type = type
        self.only_off_disk = only_off_disk

    def calculate_distance(self):
        raise NotImplementedError


class SphericalScreen(BaseScreen):
    """
    Context manager to interpret 2D coordinates as being on the inside of a spherical screen.

    The radius of the screen is the distance between the specified ``center`` and Sun center.
    This ``center`` does not have to be the same as the observer location for the coordinate
    frame.  If they are the same, then this context manager is equivalent to assuming that the
    helioprojective "zeta" component is zero.

    This replaces the default assumption where 2D coordinates are mapped onto the surface of the
    Sun.

    Parameters
    ----------
    center : `~astropy.coordinates.SkyCoord`
        The center of the spherical screen
    only_off_disk : `bool`, optional
        If `True`, apply this assumption only to off-disk coordinates, with on-disk coordinates
        still mapped onto the surface of the Sun.  Defaults to `False`.

    Examples
    --------
    .. minigallery:: sunpy.coordinates.Helioprojective.assume_spherical_screen

    >>> import astropy.units as u
    >>> from sunpy.coordinates import Helioprojective
    >>> h = Helioprojective(range(7)*u.arcsec*319, [0]*7*u.arcsec,
    ...                     observer='earth', obstime='2020-04-08')
    >>> print(h.make_3d())
    <Helioprojective Coordinate (obstime=2020-04-08T00:00:00.000, rsun=695700.0 km, observer=<HeliographicStonyhurst Coordinate for 'earth'>): (Tx, Ty, distance) in (arcsec, arcsec, AU)
        [(   0., 0., 0.99660825), ( 319., 0., 0.99687244),
            ( 638., 0., 0.99778472), ( 957., 0., 1.00103285),
            (1276., 0.,        nan), (1595., 0.,        nan),
            (1914., 0.,        nan)]>

    >>> with Helioprojective.assume_spherical_screen(h.observer):
    ...     print(h.make_3d())
    <Helioprojective Coordinate (obstime=2020-04-08T00:00:00.000, rsun=695700.0 km, observer=<HeliographicStonyhurst Coordinate for 'earth'>): (Tx, Ty, distance) in (arcsec, arcsec, AU)
        [(   0., 0., 1.00125872), ( 319., 0., 1.00125872),
            ( 638., 0., 1.00125872), ( 957., 0., 1.00125872),
            (1276., 0., 1.00125872), (1595., 0., 1.00125872),
            (1914., 0., 1.00125872)]>

    >>> with Helioprojective.assume_spherical_screen(h.observer, only_off_disk=True):
    ...     print(h.make_3d())
    <Helioprojective Coordinate (obstime=2020-04-08T00:00:00.000, rsun=695700.0 km, observer=<HeliographicStonyhurst Coordinate for 'earth'>): (Tx, Ty, distance) in (arcsec, arcsec, AU)
        [(   0., 0., 0.99660825), ( 319., 0., 0.99687244),
            ( 638., 0., 0.99778472), ( 957., 0., 1.00103285),
            (1276., 0., 1.00125872), (1595., 0., 1.00125872),
            (1914., 0., 1.00125872)]>
    """

    def __init__(self, center, **kwargs):
        super().__init__('spherical', **kwargs)
        self.center = center

    @property
    def center_hgs(self):
        hgs_frame = HeliographicStonyhurst(obstime=self.center.obstime)
        return self.center.transform_to(hgs_frame)

    @property
    def radius(self):
        return self.center_hgs.radius

    def calculate_distance(self, frame):
        sphere_center = self.center.transform_to(frame).cartesian
        c = sphere_center.norm()**2 - self.radius**2
        rep = frame.represent_as(UnitSphericalRepresentation)
        b = -2 * sphere_center.dot(rep)
        # Ignore sqrt of NaNs
        with np.errstate(invalid='ignore'):
            distance = ((-1*b) + np.sqrt(b**2 - 4*c)) / 2  # use the "far" solution
        return distance


class PlanarScreen(BaseScreen):
    """
    Context manager to interpret 2D coordinates as being on the inside of a planar screen.

    The plane goes through Sun center and is perpendicular to the vector between the
    specified vantage point and Sun center.

    This replaces the default assumption where 2D coordinates are mapped onto the surface of the
    Sun.

    Parameters
    ----------
    vantage_point : `~astropy.coordinates.SkyCoord`
        The vantage point that defines the orientation of the plane.
    only_off_disk : `bool`, optional
        If `True`, apply this assumption only to off-disk coordinates, with on-disk coordinates
        still mapped onto the surface of the Sun.  Defaults to `False`.
    """

    def __init__(self, vantage_point, **kwargs):
        super().__init__('planar', **kwargs)
        self.vantage_point = vantage_point

    def calculate_distance(self, frame):
        direction = self.vantage_point.transform_to(frame).cartesian
        direction = CartesianRepresentation(1, 0, 0) * frame.observer.radius - direction
        direction /= direction.norm()
        d_from_plane = frame.observer.radius * direction.x
        rep = frame.represent_as(UnitSphericalRepresentation)
        distance = d_from_plane / rep.dot(direction)
        return distance
