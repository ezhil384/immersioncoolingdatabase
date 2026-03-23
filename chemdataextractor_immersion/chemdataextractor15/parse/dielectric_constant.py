# -*- coding: utf-8 -*-
"""
chemdataextractor.parse.dielectric_constant.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parser for dielectric constant (relative permittivity).
Dimensionless quantity — no units to match, so the specifier acts as the
primary anchor to prevent false positives (e.g. DOI numbers).

"""

import logging
from lxml import etree

from . import R, I, W, Optional, merge, join
from .base import BaseSentenceParser
from ..utils import first
from .cem import cem, chemical_label, lenient_chemical_label, solvent_name
from .common import lbrct, dt, rbrct, comma
from .elements import W, I, R, T, Optional, Any, OneOrMore, Not, ZeroOrMore, SkipTo

log = logging.getLogger(__name__)

delim = R(r'^[:;\.,]$')

# ── Measurement condition sub-expressions ─────────────────────────────────────
units_hz = (R(r'^([KkMmGgTt])?Hz$') | I('hertz'))
frequency = (R(r'^\d+(\.\d+)?$') + units_hz).add_action(merge)
units_temp = (W('°') + Optional(R(r'^[CFK]\.?$')) | R(r'^K$') | R(r'^°C$') | R(r'^°F$'))
temperature_cond = (R(r'^\d+(\.\d+)?$') + units_temp).add_action(merge)

measurement_conditions_expr = (
    Optional(I('at') | I('under') | I('measured')).hide() +
    (frequency | temperature_cond | (frequency + Optional(I('and')).hide() + temperature_cond))
)('measurement_conditions').add_action(merge)

# ── Value patterns (dimensionless — no units element) ─────────────────────────
joined_range = R(r'^[\+\-–−]?\d+(\.\\d+)?(\(\d\))?[\-––-−~∼˜]\d+(\.\d+)?(\(\d\))?$')('value').add_action(join)
spaced_range = (R(r'^[\+\-–−]?\d+(\.d+)?(\(\d\))?$') +
                Optional(R('×') + (R('10') + W('−') + R(r'\d') | R(r'^10[\-–−]?\d+$'))) +
                (R(r'^[\-±–−~∼˜]$') + R(r'^[\+\-–−]?\d+(\.\d+)?(\(\d\))?$') |
                 R(r'^[\+\-–−]\d+(\.\d+)?(\(\d\))?$')))('value').add_action(join)
to_range = (ZeroOrMore(R(r'^[\+\-–−]?\d+(\.\d+)?(\(\d\))?$') +
                       Optional(R('×') + (R('10') + W('−') + R(r'\d') | R(r'^10[\-–−]?\d+$')))) +
            Optional(I('to')) + R(r'^[\+\-–−]?\d+(\.\d+)?(\(\d\))?$') +
            Optional(R('×') + (R('10') + W('−') + R(r'\d') | R(r'^10[\-–−]?\d+$'))))('value').add_action(join)
and_range = (ZeroOrMore(R(r'^[\+\-–−]?\d+(\.\d+)?(\(\d\))?$') +
                        Optional(R('×') + (R('10') + W('−') + R(r'\d') | R(r'^10[\-–−]?\d+$'))) +
                        Optional(comma)) +
             Optional(I('and') | comma) + R(r'^[\+\-–−]?\d+(\.\d+)?(\(\d\))?$') +
             Optional(R('×') + (R('10') + W('−') + R(r'\d') | R(r'^10[\-–−]?\d+$'))))('value').add_action(join)
range = (Optional((R(r'^[\+\-–−]?\d+(\.\d+)?(\(\d\))?$')) + R('×')) +
         Optional(R('10')) + Optional(R(r'^[\-–−]$')) +
         (and_range | to_range | spaced_range | joined_range)).add_action(join)
value = (Optional((R(r'^[\+\-–−]?\d+(\.\d+)?(\(\d\))?$')) + R('×')) +
         Optional(R('10')) + R(r'^[\+\-–−]?\d+(\.\d+)?(\(\d\))?$')).add_action(join)
ordinal = T('JJ').add_action(join)
power = (Optional((range | value) + R('×')) +
         ((R('10') + R(r'^[\-––-−~∼˜]$') + R(r'\d')) | R(r'^10[\-–−]?\d+$'))).add_action(join)
dc = (power | range | value | ordinal)('value')

# ── CEM helpers ───────────────────────────────────────────────────────────────
cem_prefix = (
    Optional('oxidized') +
    cem('cem') +
    Optional(delim).hide())
multi_cem = ZeroOrMore(cem_prefix + Optional(comma).hide()) + Optional(I('and') | comma).hide() + cem_prefix

# ── Specifier ─────────────────────────────────────────────────────────────────
dc_specifier = (
    (I('dielectric') + (I('constant') | I('strength'))) |
    (I('relative') + I('permittivity')) |
    I('permittivity') |
    R(r'^ε_?r?$') |
    R(r'^epsilon_?r?$')
)('specifier')

# ── Prefix (specifier + optional lead-in words) ───────────────────────────────
prefix = (
    Optional(I('the') | I('a') | I('an') | I('its') | I('with')).hide() +
    Optional(I('inherently')).hide() +
    Optional(I('excellent') | I('high') | I('low') | I('stable') | I('superior') | I('maximum') | I('highest')).hide() +
    Optional(I('initial')).hide() +
    dc_specifier +
    Optional(I('varies') + I('from')).hide() +
    Optional(W('=') | W('~') | W('≈') | W('≃') | I('of') | I('was') | I('is') | I('at') | I('as') | I('near') | I('above') | I('below')).hide() +
    Optional(I('demonstrated') | I('reported') | I('determined') | I('measured') | I('calculated') | I('known')).hide() +
    Optional(I('as') | (I('to') + I('be'))).hide() +
    Optional(I('in') + I('the') + I('range') | I('ranging')).hide() +
    Optional(I('of')).hide() +
    Optional(I('about') | I('from') | I('approximately') | I('around') | (I('high') + I('as'))
             | (I('higher') | I('lower') + I('than')) | (I('up') + I('to') | I('in') + I('excess') + I('of'))).hide())

# ── Value blocks (no units for dimensionless) ─────────────────────────────────
dc_and_value = (
    Optional(lbrct).hide() +
    dc +
    Optional(measurement_conditions_expr) +
    Optional(rbrct).hide())('dc')

dc_specifier_and_value = (
    Optional(prefix) +
    (Optional(delim).hide() +
     Optional(lbrct | I('[')).hide() +
     dc +
     Optional(measurement_conditions_expr) +
     Optional(rbrct | I(']')).hide())('dc'))

# ── Phrase patterns ───────────────────────────────────────────────────────────
prefix_cem_value = (
    prefix +
    Optional(I('the') | I('a') | I('an') | I('these') | I('those') | I('this') | I('that')).hide() +
    Optional(multi_cem | cem_prefix | lenient_chemical_label) +
    Optional(lbrct + Optional(cem_prefix | lenient_chemical_label | multi_cem) + rbrct) +
    Optional(I('is') | I('was') | I('were') | I('occurs') | I('of') | I('could') | I('can') | I('remained') | (
            I('can') + I('be') + I('assigned') + Optional(I('at') | I('to')))).hide() +
    Optional(I('reach') | I('reaching') | I('observed') | I('determined') | I('measured') |
             I('demonstrated') | I('calculated') | I('found') | I('increased') | I('expected')).hide() +
    Optional(
        I('in') + I('the') + I('range') + I('of') | I('ranging') + I('from') | I('as') | I('to') |
        I('to') + I('be') | I('about') | I('over') | (I('higher') | I('lower')) + I('than') | I('above')).hide() +
    Optional(lbrct).hide() +
    (dc_specifier_and_value | dc_and_value) +
    Optional(rbrct).hide())('dc_phrase')

cem_prefix_value = (
    (Optional(multi_cem | cem_prefix | lenient_chemical_label))
    + Optional(delim).hide()
    + Optional(I('that') | I('which') | I('was') | I('since') | I('the') | I('resulting') + I('in')).hide()
    + Optional(I('typically') | I('also')).hide()
    + Optional(prefix)
    + Optional(I('display') | I('displays') | I('exhibit') | I('exhibited') | I('exhibits') | I('exhibiting') |
               I('shows') | I('show') | I('showed') | I('gave') | I('demonstrate') | I('demonstrates') |
               I('are') | I('remains') | I('maintains') | I('delivered') | I('provided') |
               I('undergo') | I('undergoes') | I('has') | I('have') | I('having') | I('determined') |
               I('with') | I('where') | I('orders') | I('were') |
               (I('is') + Optional(I('classified') + I('as')))).hide()
    + Optional((I('reported') + I('to') + I('have')) | I('at') | I('with')).hide()
    + Optional(lbrct).hide()
    + (dc_specifier_and_value | dc_and_value)
    + Optional(rbrct).hide()
    + Optional(I('can') + I('be') + I('achieved'))
)('dc_phrase')

prefix_value_cem = (
    Optional(I('below') | I('at')).hide() +
    Optional(prefix) +
    Optional(I('is') | I('were') | I('was') | I('are')).hide() +
    SkipTo(dc_specifier_and_value | dc_and_value) +
    (dc_specifier_and_value | dc_and_value) +
    Optional(
        Optional(I('has') + I('been') + I('found')) +
        Optional(I('is') | I('were') | I('was') | I('are')) +
        Optional(I('observed') | I('determined') | I('measured') | I('calculated') | I('reported'))).hide() +
    Optional(dc_specifier_and_value | dc_and_value) +
    Optional(I('in') | I('for') | I('of')).hide() +
    Optional(I('the')).hide() +
    Optional(R(r'^[:;,]$')).hide() +
    Optional(lbrct).hide() +
    Optional(I('of')).hide() +
    SkipTo(multi_cem | cem_prefix | lenient_chemical_label) +
    (multi_cem | cem_prefix | lenient_chemical_label) +
    Optional(rbrct).hide())('dc_phrase')

value_prefix_cem = (
    Optional(I('of')) +
    (dc_specifier_and_value | dc_and_value) +
    Optional(delim).hide() +
    Optional(I('which') | I('that')).hide() +
    Optional(I('has') + I('been') | I('was') | I('is') | I('were')).hide() +
    Optional(I('found') | I('observed') | I('measured') | I('calculated') | I('determined')).hide() +
    Optional(I('likely') | I('close') | (I('can') + I('be'))).hide() +
    Optional(I('corresponds') | I('associated')).hide() +
    Optional(I('to') + I('be') | I('with') | I('is') | I('as')).hide() +
    Optional(I('the')).hide() +
    dc_specifier +
    Optional(I('of') | I('in')).hide() +
    (multi_cem | cem_prefix | lenient_chemical_label))('dc_phrase')

cem_value_prefix = (
    (multi_cem | cem_prefix | lenient_chemical_label)
    + Optional((I('is') | I('was') | I('were')) +
               Optional(I('reported') | I('found') | I('calculate') | I('measured') | I('shown') | I('found')) +
               Optional(I('to'))).hide()
    + Optional(I('display') | I('displays') | I('exhibit') | I('exhibits') | I('exhibiting') |
               I('shows') | I('show') | I('demonstrate') | I('demonstrates') |
               I('undergo') | I('undergoes') | I('has') | I('have') | I('having') | I('determined') |
               I('with') | I('where') | I('orders') |
               (I('is') + Optional(I('classified') + I('as')))).hide()
    + Optional(I('the') | I('a') | I('an')).hide()
    + Optional(I('value') | I('values')).hide()
    + Optional(I('varies') + I('from')).hide()
    + Optional(W('=') | W('~') | W('≈') | W('≃') | I('was') | I('is') | I('at') | I('as') |
               I('near') | I('above') | I('below')).hide()
    + Optional(I('in') + I('the') + I('range') | I('ranging')).hide()
    + Optional(I('of') | I('about') | I('from') | I('approximately') | I('around') |
               (I('high') + I('as')) | (I('higher') | I('lower') + I('than'))).hide()
    + (dc_specifier_and_value | dc_and_value)
    + Optional(I('as') | I('of') | I('for')).hide()
    + Optional(I('its') | I('their') | I('the')).hide()
    + dc_specifier)('dc_phrase')

bc = (
    prefix_value_cem
    | prefix_cem_value
    | value_prefix_cem
    | cem_value_prefix
    | cem_prefix_value
)


def print_tree(trees):
    print(trees)
    try:
        print(etree.tostring(trees))
    except BaseException:
        print('no tree')


class DielectricConstantParser(BaseSentenceParser):
    """"""
    root = bc

    def interpret(self, result, start, end):
        compound = self.model.fields['compound'].model_class()
        raw_value = first(result.xpath('./dc/value/text()'))
        # Dimensionless — no units in the grammar; raw_units will be None
        raw_units = None
        try:
            specifier = ' '.join(
                [i for i in (first(result.xpath('./specifier'))).itertext()])
        except BaseException:
            specifier = ''
        try:
            measurement_conditions = ' '.join(result.xpath('./dc/measurement_conditions/text()'))
            if not measurement_conditions:
                measurement_conditions = None
        except BaseException:
            measurement_conditions = None
        dielectric_constant = self.model(
            raw_value=raw_value,
            raw_units=raw_units,
            specifier=specifier,
            value=self.extract_value(raw_value),
            error=self.extract_error(raw_value),
            units=self.extract_units(raw_units),
            measurement_conditions=measurement_conditions,
        )
        cem_lists = []
        for cem_el in result.xpath('./cem'):
            if cem_el is not None:
                log.debug(etree.tostring(cem_el))
                cem_lists.append(''.join(cem_el.xpath('./names/text()')))
            dielectric_constant.compound = compound
            dielectric_constant.compound.names = cem_lists
            dielectric_constant.compound.labels = cem_el.xpath('./labels/text()')
            log.debug(dielectric_constant.serialize())
        yield dielectric_constant
