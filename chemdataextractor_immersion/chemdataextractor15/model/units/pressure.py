# -*- coding: utf-8 -*-
"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Units and models for pressure.

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
from .mass import Mass
from .length import Length
from .time import Time

log = logging.getLogger(__name__)


class Pressure(Dimension):
    """
    Dimension subclass for pressure.
    """
    constituent_dimensions = Mass() / Length() / Time()**2


class PressureModel(QuantityModel):
    """
    Model for pressure.
    """
    dimensions = Pressure()


class PressureUnit(Unit):
    """
    Base class for units with dimensions of pressure.
    """

    def __init__(self, magnitude=0.0, powers=None):
        super(PressureUnit, self).__init__(Pressure(), magnitude, powers)


class Pascal(PressureUnit):
    """
    class for pascal.
    """

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


class KiloPascal(PressureUnit):
    """
    class for kilopascal.
    """

    def convert_value_to_standard(self, value):
        return value * 1000

    def convert_value_from_standard(self, value):
        return value / 1000

    def convert_error_to_standard(self, error):
        return error * 1000

    def convert_error_from_standard(self, error):
        return error / 1000


class MegaPascal(PressureUnit):
    """
    class for megapascal.
    """

    def convert_value_to_standard(self, value):
        return value * 1000000

    def convert_value_from_standard(self, value):
        return value / 1000000

    def convert_error_to_standard(self, error):
        return error * 1000000

    def convert_error_from_standard(self, error):
        return error / 1000000


units_dict = {R('(P|p)(a)(s)?', group=0): Pascal,
              R('k(P|p)(a)(s)?', group=0): KiloPascal,
              R('M(P|p)(a)(s)?', group=0): MegaPascal}
Pressure.units_dict = units_dict
