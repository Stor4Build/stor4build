# SPDX-FileCopyrightText: 2023-present Alliance for Sustainable Energy, LLC and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from enum import Enum, auto

from scp.ethyl_alcohol import EthylAlcohol
from scp.ethylene_glycol import EthyleneGlycol
from scp.methyl_alcohol import MethylAlcohol
from scp.propylene_glycol import PropyleneGlycol
from scp.water import Water as ScpWater


class FluidType(Enum):
    EthylAlcohol = 1
    EthyleneGlycol = 2
    MethylAlcohol = 3
    PropyleneGlycol = 4
    Water = 5
    SimpleWater = 6
    PCM2X2A = 7
    PCM1X1A = 8

class PCM1X1A:
    def freeze_point(self, _=None) -> float:
        return 2.0
    def density(self, temp:float) -> float:
        return 770.0
    def specific_heat(self, temp: float) -> float:
        return 2000.0
    def enthalpy_of_fusion(self) -> float:
        return 200000.0
    def solid_specific_heat(self) -> float:
        return 2000.0

class PCM2X2A:
    def freeze_point(self, _=None) -> float:
        return 2.0
    def density(self, temp:float) -> float:
        return 770.0
    def specific_heat(self, temp: float) -> float:
        return 2000.0
    def enthalpy_of_fusion(self) -> float:
        return 200000.0
    def solid_specific_heat(self) -> float:
        return 2000.0

class SimpleWater:
    def freeze_point(self, _=None) -> float:
        return 0.0
    def density(self, temp:float) -> float:
        return 1000.0
    def specific_heat(self, temp: float) -> float:
        return 4184.0
    def enthalpy_of_fusion(self) -> float:
        return 334000.0
    def solid_specific_heat(self) -> float:
        return 2030.0

class Water(ScpWater):
    def enthalpy_of_fusion(self) -> float:
        return 334000
    def solid_specific_heat(self) -> float:
        return 2030.0

def get_storage_medium(fluid_type, concentration=None):
    if fluid_type == FluidType.Water:
        return Water()
    elif fluid_type == FluidType.SimpleWater:
        return SimpleWater()
    elif fluid_type == FluidType.PCM2X2A:
        return PCM2X2A()
    else:
        raise ValueError("Fluid type not recognized")

def get_fluid(fluid_type, concentration=None):
    if fluid_type == FluidType.EthylAlcohol:
        return EthylAlcohol(concentration)
    elif fluid_type == FluidType.EthyleneGlycol:
        return EthyleneGlycol(concentration)
    elif fluid_type == FluidType.MethylAlcohol:
        return MethylAlcohol(concentration)
    elif fluid_type == FluidType.PropyleneGlycol:
        return PropyleneGlycol(concentration)
    elif fluid_type == FluidType.Water:
        return Water()
    elif fluid_type == FluidType.SimpleWater:
        return SimpleWater()
    elif fluid_type == FluidType.PCM2X2A:
        return PCM2X2A()
    elif fluid_type == FluidType.PCM1X1A:
        return PCM1X1A()
    else:
        raise ValueError("Fluid type not recognized")
