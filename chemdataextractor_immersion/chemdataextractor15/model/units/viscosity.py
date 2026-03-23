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
    class for cP.
    """

    def convert_value_to_standard(self, value):
        return value / 1000

    def convert_value_from_standard(self, value):
        return value * 1000

    def convert_error_to_standard(self, error):
        return error / 1000

    def convert_error_from_standard(self, error):
        return error * 1000


units_dict = {
    R(r'Pa\.s', group=0): PaSecond,
    R(r'Pa\*s', group=0): PaSecond,
    R(r'mPa\.s', group=0): MilliPaSecond,
    R(r'mPa\*s', group=0): MilliPaSecond,
    R(r'cP', group=0): CentiPoise
}
ViscosityUnit.units_dict = units_dict
