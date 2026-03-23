# -*- coding: utf-8 -*-
"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Units and models for power.

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


class Power(Dimension):
    """
    Dimension subclass for power.
    """
    constituent_dimensions = Mass() * Length()**2 / Time()**3


class PowerModel(QuantityModel):
    """
    Model for power.
    """
    dimensions = Power()


class PowerUnit(Unit):
    """
    Base class for units with dimensions of power.
    """

    def __init__(self, magnitude=0.0, powers=None):
        super(PowerUnit, self).__init__(Power(), magnitude, powers)


class Watt(PowerUnit):
    """
    class for watt.
    """

    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


units_dict = {R('(W|w)(att(s)?)?', group=0): Watt}
Power.units_dict = units_dict
