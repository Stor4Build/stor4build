# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
from marshmallow import Schema, fields, validate, EXCLUDE, post_load
from .osmeasures import climate_zone_list, vintage_list, prototypes_list
from dataclasses import dataclass
from typing import List
import json
import re

class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE
    @post_load
    def promote(self, data, **kwargs):
        return self.promote_to(**data)

@dataclass
class UtilityRate:
    rate: float
    unit: str
    period: int
    
class UtilityRateSchema(BaseSchema):
    rate = fields.Float(validate=lambda x: x >= 0.0, required=True)
    unit = fields.Str(required=True)
    period = fields.Int(validate=lambda x: x > 0, required=True)
    promote_to = UtilityRate

@dataclass
class MonthSchedule:
    unit: str
    month: str
    periods: List[int]

class MonthScheduleSchema(BaseSchema):
    unit = fields.Str(required=True)
    month = fields.Str(required=True)
    periods = fields.List(fields.Int(), required=True)
    promote_to = MonthSchedule

@dataclass
class Schedule:
    months: List[MonthSchedule]

class ScheduleSchema(BaseSchema):
    months = fields.List(fields.Nested(lambda: MonthScheduleSchema()))
    promote_to = Schedule

@dataclass
class UtilityData:
    costs: List[UtilityRate]
    schedule: Schedule

class UtilityDataSchema(BaseSchema):
    costs = fields.List(fields.Nested(lambda: UtilityRateSchema()))
    schedule = fields.Nested(lambda: ScheduleSchema(), required=True)
    promote_to = UtilityData

@dataclass
class BuildingData:
    climate: str
    vintage: int
    type: str

class BuildingDataSchema(BaseSchema):
    climate = fields.Str(validate=validate.OneOf(climate_zone_list), required=True)
    vintage = fields.Int(required=True)
    type = fields.Str(validate=validate.OneOf(prototypes_list), required=True)
    promote_to = BuildingData

hm_grouper = re.compile(r"^([0-2][0-3]):([0-5][0-9])$")
hm_matcher = re.compile(r"^[0-2][0-3]:[0-5][0-9]$")

@dataclass
class HourMinute:
    hour: int
    minute: int = 0
    
class HourMinuteSchema(Schema):
    hour_minute = fields.Str(validate=validate.Regexp(r"^[0-2][0-3]:[0-5][0-9]$"),
                             required=True)
    @post_load
    def promote(self, data, **kwargs):
        print(data)
        return self.HourMinute(hour=0, minute=0)

@dataclass
class Interval:
    begin: HourMinute
    end: HourMinute

# r"^[0-2][0-3]:[0-5][0-9]$"gm
# r"^[0-2][0-3]:00$"gm
class IntervalSchema(Schema):
    begin = fields.Str(validate=validate.Regexp(hm_matcher), required=True)
    end = fields.Str(validate=validate.Regexp(hm_matcher), required=True)
    
    @post_load
    def promote(self, data, **kwargs):
        return self.promote_to(**data)

@dataclass
class StorageData:
    type: str
    capacity: float
    charge_interval: Interval = None
    discharge_interval: Interval = None

class StorageDataSchema(BaseSchema):
    type = fields.Str(validate=validate.OneOf(['ThermalTank-Ice', 'ThermalTank-ChilledWater']), required=True)
    capacity = fields.Float(validate=lambda x: x > 0.0 and x <= 100.0, required=True)
    charge_interval = fields.Nested(lambda: IntervalSchema(), required=False)
    discharge_interval = fields.Nested(lambda: IntervalSchema(), required=False)
    promote_to = StorageData

@dataclass
class InputData:
    baseline: BuildingData
    storage: StorageData
    energy: UtilityData
    demand: UtilityData
    
    @classmethod
    def load(cls, data):
        schema = InputDataSchema()
        return schema.load(data)
        
    @classmethod
    def read(cls, input_path):
        with open(input_path, 'r') as fp:
            data = json.load(fp)
        return cls.load(data)

class InputDataSchema(BaseSchema):
    baseline = fields.Nested(lambda: BuildingDataSchema(), required=True)
    storage = fields.Nested(lambda: StorageDataSchema(), required=True)
    energy = fields.Nested(lambda: UtilityDataSchema(), required=True)
    demand = fields.Nested(lambda: UtilityDataSchema(), required=True)
    promote_to = InputData
