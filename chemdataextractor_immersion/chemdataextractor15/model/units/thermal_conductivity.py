# -*- coding: utf-8 -*-
"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Units and models for thermal conductivity.

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
from .power import Power
from .length import Length
from .temperature import Temperature

log = logging.getLogger(__name__)


class ThermConductivity(Dimension):
    """
    Dimension subclass for thermal conductivity.
    """
    constituent_dimensions = Power() / Length() / Temperature()


class ThermConductivityModel(QuantityModel):
    """
    Model for thermal conductivity.
    """
    dimensions = ThermConductivity()


class ThermConductivityUnit(Unit):
    """
    Base class for units with dimensions of thermal conductivity.
    """

    def __init__(self, magnitude=0.0, powers=None):
        super(ThermConductivityUnit, self).__init__(ThermConductivity(), magnitude, powers)


class ThermConductivityUnits(ThermConductivityUnit):
    """
    class for thermal conductivity units.
    """

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


units_dict = {
    R(r'W/mK', group=0): ThermConductivityUnits,
    R(r'Wm[\-–−]1K[\-–−]1', group=0): ThermConductivityUnits,
    R(r'W/m/K', group=0): ThermConductivityUnits
}
ThermConductivityUnit.units_dict = units_dict
