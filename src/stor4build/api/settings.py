# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import os
from functools import lru_cache
from typing import Mapping, Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

this_dir = os.path.abspath(os.path.dirname(__file__))
default_measures_dir = os.path.join(this_dir, "..", "..", "..", "measures")


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FLASK_", extra="ignore", populate_by_name=True)

    openstudio: str = Field("openstudio", validation_alias=AliasChoices("OPENSTUDIO", "openstudio"))
    measures_directory: str = Field(default_measures_dir, validation_alias=AliasChoices("MEASURES_DIRECTORY", "measures_directory"))
    timescale_host: str = Field("timescale", validation_alias=AliasChoices("TIMESCALE_HOST", "timescale_host"))
    timescale_port: str = Field("5432", validation_alias=AliasChoices("TIMESCALE_PORT", "timescale_port"))
    cache_baseline: bool = Field(False, validation_alias=AliasChoices("CACHE_BASELINE", "cache_baseline"))
    store_missing_results: bool = Field(True, validation_alias=AliasChoices("STORE_MISSING_RESULTS", "store_missing_results"))
    oldest_acceptable: Optional[str] = Field(None, validation_alias=AliasChoices("OLDEST_ACCEPTABLE", "oldest_acceptable"))
    run_directory: Optional[str] = Field(None, validation_alias=AliasChoices("RUN_DIRECTORY", "run_directory"))
    noisy: bool = Field(True, validation_alias=AliasChoices("NOISY", "noisy"))

    timescale_db: str = Field(..., validation_alias=AliasChoices("TIMESCALE_DB", "timescale_db"))
    timescale_username: str = Field(..., validation_alias=AliasChoices("TIMESCALE_USERNAME", "timescale_username"))
    timescale_password: str = Field(..., validation_alias=AliasChoices("TIMESCALE_PASSWORD", "timescale_password"))

    @property
    def resolved_measures_directory(self) -> str:
        return os.path.abspath(self.measures_directory)

    @property
    def resolved_run_directory(self) -> Optional[str]:
        if self.run_directory is None:
            return None
        return os.path.abspath(self.run_directory)


@lru_cache(maxsize=1)
def get_settings_from_environment() -> APISettings:
    return APISettings()


def load_settings(config: Optional[Mapping[str, object]] = None) -> APISettings:
    if config is None:
        return get_settings_from_environment()
    return APISettings(**dict(config))
