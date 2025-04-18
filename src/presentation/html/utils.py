from datetime import datetime, timedelta

import pytz
from fastapi.templating import Jinja2Templates

from src.domain.constant import SeverityEnum
from src.domain.entity import Finding

templates = Jinja2Templates("src/presentation/html/templates/")


# create decorator for this
def startsWith(text: str, word: str):
    if not text or not word:
        return False
    return text.startswith(word)


def findingSeverityMap(status: SeverityEnum):
    dct = {
        SeverityEnum.CRITICAL: "maroon",
        SeverityEnum.HIGH: "red",
        SeverityEnum.MEDIUM: "orange",
        SeverityEnum.LOW: "green",
    }
    return dct.get(status)


def timedelta_filter(val, days=0):
    return val + timedelta(days=days)


def slaCalc(finding: Finding, sla: dict):
    severity = finding.severity.value
    return (
        finding.finding_date + timedelta(sla.get(severity, 0)) - datetime.now(pytz.utc)
    ).days


def datetime_format(value, format="%H:%M %d-%m-%y"):
    if value:
        return value.strftime(format)


templates.env.filters["startsWith"] = startsWith
templates.env.filters["findingSeverityMap"] = findingSeverityMap
templates.env.filters["slaCalc"] = slaCalc
templates.env.filters["datetime_format"] = datetime_format
