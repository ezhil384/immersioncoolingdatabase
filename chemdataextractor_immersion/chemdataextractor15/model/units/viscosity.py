# -*- coding: utf-8 -*-
"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Units and models for viscosity.

SHu Huang
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .quantity_model import QuantityModel
from .unit import Unit
from .dimension import Dimension
from ...parse.elements import R
import logging
from .pressure import Pressure
from .time import Time

log = logging.getLogger(__name__)


class Viscosity(Dimension):
    """
    Dimension subclass for viscosity.
    """
    constituent_dimensions = Pressure() * Time()


class ViscosityModel(QuantityModel):
    """
    Model for viscosity.
    """
    dimensions = Viscosity()


class ViscosityUnit(Unit):
    """
    Base class for units with dimensions of viscosity.
    """

    def __init__(self, magnitude=0.0, powers=None):
        super(ViscosityUnit, self).__init__(Viscosity(), magnitude, powers)


class PaSecond(ViscosityUnit):
    """
    class for Pa.s.
    """

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


class MilliPaSecond(ViscosityUnit):
    """
    class for mPa.s.
    """

    def convert_value_to_standard(self, value):
        return value / 1000

    def convert_value_from_standard(self, value):
        return value * 1000

    def convert_error_to_standard(self, error):
        return error / 1000

    def convert_error_from_standard(self, error):
        return error * 1000


class CentiPoise(ViscosityUnit):
    """
    class for cP (= mPa·s, dynamic viscosity).
    """

    def convert_value_to_standard(self, value):
        return value / 1000

    def convert_value_from_standard(self, value):
        return value * 1000

    def convert_error_to_standard(self, error):
        return error / 1000

    def convert_error_from_standard(self, error):
        return error * 1000


class CentiStokes(ViscosityUnit):
    """
    Class for cSt (centistokes, kinematic viscosity).
    1 cSt = 1 mm²/s = 1e-6 m²/s.
    Stored as-is; dimensional conversion relative to Pa·s is not meaningful
    but raw_value/raw_units are preserved for downstream use.
    """

    def convert_value_to_standard(self, value):
        return value * 1e-6

    def convert_value_from_standard(self, value):
        return value / 1e-6

    def convert_error_to_standard(self, error):
        return error * 1e-6

    def convert_error_from_standard(self, error):
        return error / 1e-6


class Stokes(ViscosityUnit):
    """
    Class for St (stokes, kinematic viscosity).
    1 St = 100 cSt = 1e-4 m²/s.
    """

    def convert_value_to_standard(self, value):
        return value * 1e-4

    def convert_value_from_standard(self, value):
        return value / 1e-4

    def convert_error_to_standard(self, error):
        return error * 1e-4

    def convert_error_from_standard(self, error):
        return error / 1e-4


class SquareMilliMeterPerSecond(ViscosityUnit):
    """
    Class for mm²/s (kinematic viscosity, SI-adjacent).
    1 mm²/s = 1 cSt = 1e-6 m²/s.
    """

    def convert_value_to_standard(self, value):
        return value * 1e-6

    def convert_value_from_standard(self, value):
        return value / 1e-6

    def convert_error_to_standard(self, error):
        return error * 1e-6

    def convert_error_from_standard(self, error):
        return error / 1e-6


units_dict = {
    R(r'Pa\.s', group=0): PaSecond,
    R(r'Pa\*s', group=0): PaSecond,
    R(r'mPa\.s', group=0): MilliPaSecond,
    R(r'mPa\*s', group=0): MilliPaSecond,
    R(r'cP', group=0): CentiPoise,
    R(r'cSt', group=0): CentiStokes,
    R(r'St', group=0): Stokes,
    R(r'mm[²2][\/]s', group=0): SquareMilliMeterPerSecond,
    R(r'mm[²2]s[\-−]1', group=0): SquareMilliMeterPerSecond,
}
ViscosityUnit.units_dict = units_dict
