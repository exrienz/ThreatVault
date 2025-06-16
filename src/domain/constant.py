from enum import Enum
from typing import Protocol

import pandas as pd
import polars as pl


class SeverityEnum(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EnvEnum(Enum):
    PRODUCTION = "Production"
    NON_PRODUCTION = "Non-Production"


class FnStatusEnum(Enum):
    NEW = "NEW"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    EXEMPTION = "EXEMPTION"
    OTHERS = "OTHERS"


# class RoleEnum(Enum):
#     Admin = "Admin"
#     ITSE = "ITSE"
#     Management = "Management"
#     Audit = "Audit"
#     Owner = "Owner"
#     Custom = "Custom"


class PluginFunction(Protocol):
    def process(self, file: bytes) -> pl.LazyFrame | pl.DataFrame | pd.DataFrame: ...
