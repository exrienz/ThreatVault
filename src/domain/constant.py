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


# Deprecated
class FnStatusEnum(Enum):
    NEW = "NEW"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    EXEMPTION = "EXEMPTION"
    OTHERS = "OTHERS"


class VAStatusEnum(Enum):
    NEW = "NEW"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    EXEMPTION = "EXEMPTION"
    OTHERS = "OTHERS"


class HAStatusEnum(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"


# TODO: Default Role
# class RoleEnum(Enum):
#     Admin = "Admin"
#     ITSE = "ITSE"
#     Management = "Management"
#     Audit = "Audit"
#     Owner = "Owner"
#     Custom = "Custom"


class ApiKeyTypeEnum(Enum):
    Global = "global"
    Product = "product"


class PluginFunction(Protocol):
    def process(
        self, file: bytes, file_type: str
    ) -> pl.LazyFrame | pl.DataFrame | pd.DataFrame: ...
