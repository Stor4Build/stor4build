# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from marshmallow import Schema, fields, validate, EXCLUDE, post_load
from .osmeasures import climate_zone_list, vintage_list, prototypes_list
from dataclasses import dataclass
from typing import List
import json
import datetime

actual_climate_zone_list = climate_zone_list[:]
actual_climate_zone_list.remove('5C')
actual_prototypes_list = ['LargeOffice', 'SmallOffice', 'RetailStandalone']

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
    
    def find_peak_window(self, peak:int) -> (int,int):
        reverse_sch = list(reversed(self.periods)) # This is probably bad, just do it for now
        start_index = self.periods.index(peak)
        start_hour = start_index + 1
        end_hour = len(self.periods) - reverse_sch.index(peak)
        v = set(self.periods[start_index:end_hour])
        if len(v) > 1:
            return None
        if v.pop() != peak:
            return None
        return start_hour, end_hour

    def rate_array(self, costs):
        result = []
        for v in self.periods:
            if v in costs:
                result.append(costs[v].rate)
            else:
                return None
        return result
        
    def period_array(self, costs):
        result = []
        for v in self.periods:
            if v in costs:
                result.append(costs[v].period)
            else:
                return None
        return result

class MonthScheduleSchema(BaseSchema):
    unit = fields.Str(required=True)
    month = fields.Str(required=True)
    periods = fields.List(fields.Int(), required=True)
    promote_to = MonthSchedule

class Schedule:
    def __init__(self, months: List[MonthSchedule]):
        self.months = {}
        # Duplicates will get overridden here
        for month in months:
            self.months[month.month] = month

class ScheduleSchema(BaseSchema):
    months = fields.List(fields.Nested(lambda: MonthScheduleSchema()))
    promote_to = Schedule

class UtilityData:
    def __init__(self, costs: List[UtilityRate], schedule: Schedule):
        self.costs = {}
        for cost in costs:
            self.costs[cost.period] = cost
        self.schedule = schedule
        
    def rate_schedule(self, start: datetime.date, end: datetime.date):
        # For now, assume only "All" is present
        ndays = (end-start).days + 1
        return self.schedule.months['All'].rate_array(self.costs) * ndays
        
    def demand_schedule(self, start: datetime.date, end: datetime.date):
        # For now, assume only "All" is present
        ndays = (end-start).days + 1
        # Force the array to contain 0..len(costs)-1
        thelist = list(self.costs.values())
        thelist.sort(key=lambda x: x.rate)
        for i,c in enumerate(thelist):
            c.period = i
        return self.schedule.months['All'].period_array(self.costs) * ndays

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
    climate = fields.Str(validate=validate.OneOf(actual_climate_zone_list), required=True)
    vintage = fields.Int(required=True)
    type = fields.Str(validate=validate.OneOf(actual_prototypes_list), required=True)
    promote_to = BuildingData

@dataclass
class HourMinute:
    hour: int
    minute: int = 0
    def __str__(self):
        return '%02d:%02d' % (self.hour, self.minute)
    
class HourMinuteSchema(BaseSchema):
    hour = fields.Int(validate=validate.Range(min=0, max=23),
                      required=True)
    promote_to = HourMinute

@dataclass
class Interval:
    begin: HourMinute
    end: HourMinute

class IntervalSchema(BaseSchema):
    begin = fields.Nested(lambda: HourMinuteSchema(), required=True)
    end = fields.Nested(lambda: HourMinuteSchema(), required=True)
    promote_to = Interval

@dataclass
class StorageData:
    type: str
    capacity: float = 100.0
    charge_interval: Interval = None
    discharge_interval: Interval = None
    size_fraction: float = 1.0

class StorageDataSchema(BaseSchema):
    type = fields.Str(validate=validate.OneOf(['ThermalTank-Ice', 'ThermalTank-ChilledWater', 'PackagedIceStorage']), required=True)
    capacity = fields.Float(validate=lambda x: x > 0.0 and x <= 100.0, required=False)
    charge_interval = fields.Nested(lambda: IntervalSchema(), required=False)
    discharge_interval = fields.Nested(lambda: IntervalSchema(), required=False)
    size_fraction = fields.Float(validate=validate.OneOf([1.0, 0.9, 0.8, 0.7, 0.6, 0.5]), required=False)
    promote_to = StorageData

@dataclass
class InputData:
    baseline: BuildingData
    storage: StorageData
    energy: UtilityData = None
    demand: UtilityData = None
    
    @classmethod
    def load(cls, data, ):
        schema = InputDataSchema()
        return schema.load(data)
        
    @classmethod
    def load_tessbed_v1(cls, data, ):
        schema = TESSBeDv1Schema()
        return schema.load(data)
        
    @classmethod
    def read(cls, input_path):
        with open(input_path, 'r') as fp:
            data = json.load(fp)
        return cls.load(data)
    
class InputDataSchema(BaseSchema):
    baseline = fields.Nested(lambda: BuildingDataSchema(), required=True)
    storage = fields.Nested(lambda: StorageDataSchema(), required=True)
    energy = fields.Nested(lambda: UtilityDataSchema(), required=False)
    demand = fields.Nested(lambda: UtilityDataSchema(), required=False)
    promote_to = InputData
    
class TESSBeDv1Schema(BaseSchema):
    baseline = fields.Nested(lambda: BuildingDataSchema(), required=True)
    storage = fields.Nested(lambda: StorageDataSchema(), required=True)
    energy = fields.Nested(lambda: UtilityDataSchema(), required=True)
    demand = fields.Nested(lambda: UtilityDataSchema(), required=False)
    promote_to = InputData
