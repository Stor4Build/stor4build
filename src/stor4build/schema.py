from __future__ import annotations

# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from dataclasses import dataclass
import json
import datetime
from typing import List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .osmeasures import climate_zone_list, supported_prototypes_list, dxcoil_supported

actual_climate_zone_list = climate_zone_list[:]
actual_climate_zone_list.remove("5C")
actual_prototypes_list = supported_prototypes_list

FULL_STORAGE_TYPES = [
    "ThermalTank-Ice",
    "ThermalTank-ChilledWater",
    "PackagedIceStorage",
]
SIMPLIFIED_STORAGE_TYPES = FULL_STORAGE_TYPES + ["ice", "water", "pcm-1"]
SIZE_FRACTIONS = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
STORAGE_MEDIA = ["water", "pcm2x2a"]


class PayloadModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


@dataclass
class UtilityRate:
    rate: float
    unit: str
    period: int


class UtilityRatePayload(PayloadModel):
    rate: float = Field(..., ge=0.0)
    unit: str
    period: int = Field(..., gt=0)

    def to_domain(self) -> UtilityRate:
        return UtilityRate(rate=self.rate, unit=self.unit, period=self.period)


@dataclass
class MonthSchedule:
    unit: str
    month: str
    periods: List[int]

    def find_peak_window(self, peak: int) -> Optional[Tuple[int, int]]:
        reverse_sch = list(reversed(self.periods))
        start_index = self.periods.index(peak)
        start_hour = start_index + 1
        end_hour = len(self.periods) - reverse_sch.index(peak)
        values = set(self.periods[start_index:end_hour])
        if len(values) > 1:
            return None
        if values.pop() != peak:
            return None
        return start_hour, end_hour

    def rate_array(self, costs) -> Optional[List[float]]:
        result = []
        for value in self.periods:
            if value in costs:
                result.append(costs[value].rate)
            else:
                return None
        return result

    def period_array(self, costs) -> Optional[List[int]]:
        result = []
        for value in self.periods:
            if value in costs:
                result.append(costs[value].period)
            else:
                return None
        return result


class MonthSchedulePayload(PayloadModel):
    unit: str
    month: str
    periods: List[int]

    def to_domain(self) -> MonthSchedule:
        return MonthSchedule(unit=self.unit, month=self.month, periods=list(self.periods))


class Schedule:
    def __init__(self, months: List[MonthSchedule]):
        self.months = {}
        for month in months:
            self.months[month.month] = month


class SchedulePayload(PayloadModel):
    months: List[MonthSchedulePayload] = Field(default_factory=list)

    def to_domain(self) -> Schedule:
        return Schedule([month.to_domain() for month in self.months])


class UtilityData:
    def __init__(self, costs: List[UtilityRate], schedule: Schedule):
        self.costs = {}
        for cost in costs:
            self.costs[cost.period] = cost
        self.schedule = schedule

    def rate_schedule(self, start: datetime.date, end: datetime.date):
        ndays = (end - start).days + 1
        return self.schedule.months["All"].rate_array(self.costs) * ndays

    def demand_schedule(self, start: datetime.date, end: datetime.date):
        ndays = (end - start).days + 1
        sorted_costs = list(self.costs.values())
        sorted_costs.sort(key=lambda value: value.rate)
        for index, cost in enumerate(sorted_costs):
            cost.period = index
        return self.schedule.months["All"].period_array(self.costs) * ndays


class UtilityDataPayload(PayloadModel):
    costs: List[UtilityRatePayload] = Field(default_factory=list)
    schedule: SchedulePayload

    def to_domain(self) -> UtilityData:
        return UtilityData(
            costs=[cost.to_domain() for cost in self.costs],
            schedule=self.schedule.to_domain(),
        )


@dataclass
class BuildingData:
    climate: str
    vintage: int
    type: str


class BuildingDataPayload(PayloadModel):
    climate: str = Field(..., json_schema_extra={"enum": actual_climate_zone_list})
    vintage: int
    type: str = Field(..., json_schema_extra={"enum": actual_prototypes_list})

    @model_validator(mode="after")
    def validate_choices(self) -> "BuildingDataPayload":
        if self.climate not in actual_climate_zone_list:
            raise ValueError(f"Input should be one of: {', '.join(actual_climate_zone_list)}")
        if self.type not in actual_prototypes_list:
            raise ValueError(f"Input should be one of: {', '.join(actual_prototypes_list)}")
        return self

    def to_domain(self) -> BuildingData:
        return BuildingData(climate=self.climate, vintage=self.vintage, type=self.type)


@dataclass
class HourMinute:
    hour: int
    minute: int = 0

    def __str__(self) -> str:
        return "%02d:%02d" % (self.hour, self.minute)


class HourMinutePayload(PayloadModel):
    hour: int = Field(..., ge=0, le=23)

    def to_domain(self) -> HourMinute:
        return HourMinute(hour=self.hour)


@dataclass
class Interval:
    begin: HourMinute
    end: HourMinute


class IntervalPayload(PayloadModel):
    begin: HourMinutePayload
    end: HourMinutePayload

    def to_domain(self) -> Interval:
        return Interval(begin=self.begin.to_domain(), end=self.end.to_domain())


@dataclass
class StorageData:
    type: str
    capacity: float = 100.0
    charge_interval: Optional[Interval] = None
    discharge_interval: Optional[Interval] = None
    size_fraction: float = 1.0
    medium: str = "water"


class StorageDataPayload(PayloadModel):
    type: str = Field(..., json_schema_extra={"enum": FULL_STORAGE_TYPES})
    capacity: float = Field(default=100.0, gt=0.0, le=100.0)
    charge_interval: Optional[IntervalPayload] = None
    discharge_interval: Optional[IntervalPayload] = None
    size_fraction: float = Field(default=1.0, json_schema_extra={"enum": SIZE_FRACTIONS})
    medium: str = Field(default="water", json_schema_extra={"enum": STORAGE_MEDIA})

    @model_validator(mode="after")
    def validate_choices(self) -> "StorageDataPayload":
        if self.type not in FULL_STORAGE_TYPES:
            raise ValueError(f"Input should be one of: {', '.join(FULL_STORAGE_TYPES)}")
        if self.size_fraction not in SIZE_FRACTIONS:
            raise ValueError(f"Input should be one of: {', '.join(str(value) for value in SIZE_FRACTIONS)}")
        if self.medium not in STORAGE_MEDIA:
            raise ValueError(f"Input should be one of: {', '.join(STORAGE_MEDIA)}")
        return self

    def to_domain(self) -> StorageData:
        return StorageData(
            type=self.type,
            capacity=self.capacity,
            charge_interval=None if self.charge_interval is None else self.charge_interval.to_domain(),
            discharge_interval=None if self.discharge_interval is None else self.discharge_interval.to_domain(),
            size_fraction=self.size_fraction,
            medium=self.medium,
        )


class SimplifiedStorageDataPayload(PayloadModel):
    type: str = Field(..., json_schema_extra={"enum": SIMPLIFIED_STORAGE_TYPES})
    capacity: float = Field(default=100.0, gt=0.0, le=100.0)
    charge_interval: Optional[IntervalPayload] = None
    discharge_interval: Optional[IntervalPayload] = None
    size_fraction: float = Field(default=1.0, json_schema_extra={"enum": SIZE_FRACTIONS})
    medium: Optional[str] = Field(default=None, json_schema_extra={"enum": STORAGE_MEDIA})

    @model_validator(mode="after")
    def validate_choices(self) -> "SimplifiedStorageDataPayload":
        if self.type not in SIMPLIFIED_STORAGE_TYPES:
            raise ValueError(f"Input should be one of: {', '.join(SIMPLIFIED_STORAGE_TYPES)}")
        if self.size_fraction not in SIZE_FRACTIONS:
            raise ValueError(f"Input should be one of: {', '.join(str(value) for value in SIZE_FRACTIONS)}")
        if self.medium is not None and self.medium not in STORAGE_MEDIA:
            raise ValueError(f"Input should be one of: {', '.join(STORAGE_MEDIA)}")
        return self

    def normalized(self, building_type: str) -> StorageDataPayload:
        storage_type = self.type
        medium = self.medium
        if storage_type == "ice":
            if building_type in dxcoil_supported:
                storage_type = "PackagedIceStorage"
            else:
                storage_type = "ThermalTank-Ice"
                medium = "water"
        elif storage_type == "water":
            if building_type in dxcoil_supported:
                raise ValueError(f'Building "{building_type}" does not support "water" storage')
            storage_type = "ThermalTank-ChilledWater"
            medium = "water"
        elif storage_type == "pcm-1":
            if building_type in dxcoil_supported:
                raise ValueError(f'Building "{building_type}" does not support "pcm-1" storage')
            storage_type = "ThermalTank-Ice"
            medium = "pcm2x2a"

        if medium is None:
            medium = "water"

        return StorageDataPayload(
            type=storage_type,
            capacity=self.capacity,
            charge_interval=self.charge_interval,
            discharge_interval=self.discharge_interval,
            size_fraction=self.size_fraction,
            medium=medium,
        )


@dataclass
class InputData:
    baseline: BuildingData
    storage: StorageData
    energy: Optional[UtilityData] = None
    demand: Optional[UtilityData] = None

    @classmethod
    def load(cls, data):
        return InputDataPayload.model_validate(data).to_domain()

    @classmethod
    def read(cls, input_path):
        with open(input_path, "r") as fp:
            data = json.load(fp)
        return cls.load(data)


class InputDataPayload(PayloadModel):
    baseline: BuildingDataPayload
    storage: SimplifiedStorageDataPayload
    energy: Optional[UtilityDataPayload] = None
    demand: Optional[UtilityDataPayload] = None

    @model_validator(mode="after")
    def normalize_storage(self) -> "InputDataPayload":
        self.storage = self.storage.normalized(self.baseline.type)
        return self

    def to_domain(self) -> InputData:
        return InputData(
            baseline=self.baseline.to_domain(),
            storage=self.storage.to_domain(),
            energy=None if self.energy is None else self.energy.to_domain(),
            demand=None if self.demand is None else self.demand.to_domain(),
        )


class SimulationRequest(InputDataPayload):
    header_style: Optional[str] = Field(
        default=None,
        json_schema_extra={"enum": ["simple", "detailed"]},
    )

    @model_validator(mode="after")
    def validate_header_style(self) -> "SimulationRequest":
        if self.header_style not in (None, "simple", "detailed"):
            raise ValueError("Input should be one of: simple, detailed")
        return self

    @property
    def detailed_header(self) -> bool:
        return self.header_style != "simple"


class _SchemaAdapter:
    payload_model = PayloadModel

    def load(self, data):
        payload = self.payload_model.model_validate(data)
        if hasattr(payload, "to_domain"):
            return payload.to_domain()
        return payload


class UtilityRateSchema(_SchemaAdapter):
    payload_model = UtilityRatePayload


class MonthScheduleSchema(_SchemaAdapter):
    payload_model = MonthSchedulePayload


class ScheduleSchema(_SchemaAdapter):
    payload_model = SchedulePayload


class UtilityDataSchema(_SchemaAdapter):
    payload_model = UtilityDataPayload


class BuildingDataSchema(_SchemaAdapter):
    payload_model = BuildingDataPayload


class HourMinuteSchema(_SchemaAdapter):
    payload_model = HourMinutePayload


class IntervalSchema(_SchemaAdapter):
    payload_model = IntervalPayload


class StorageDataSchema(_SchemaAdapter):
    payload_model = StorageDataPayload


class SimplifiedStorageDataSchema(_SchemaAdapter):
    payload_model = SimplifiedStorageDataPayload


class InputDataSchema(_SchemaAdapter):
    payload_model = InputDataPayload
