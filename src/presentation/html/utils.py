from datetime import datetime, timedelta

import pytz
from fastapi.templating import Jinja2Templates

from src.application.middlewares.user_context import current_user_perm, get_current_user
from src.config import sidebar_items
from src.domain.constant import SeverityEnum
from src.domain.entity import Finding

templates = Jinja2Templates(
    directory="src/presentation/html/templates/", trim_blocks=True, lstrip_blocks=True
)


def startsWith(text: str, word: str):
    if not text or not word:
        return False
    return text.startswith(word)


def findingSeverityMap(status: SeverityEnum | str):
    if isinstance(status, SeverityEnum):
        status_str = status.value
    else:
        status_str = status

    dct = {
        "CRITICAL": "maroon",
        "HIGH": "red",
        "MEDIUM": "orange",
        "LOW": "green",
    }
    return dct.get(status_str)


def statusBadgeMap(status: str):
    dct = {
        "failed": "maroon",
        "warning": "red",
        "exemption": "orange",
        "passed": "green",
    }
    return dct.get(status.lower(), "orange")


def assessmentTypeMap(type_: str):
    dct = {
        "VA": "VAPT",
        "HA": "Compliance",
    }
    return dct.get(type_)


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


def is_admin():
    user_info = get_current_user()
    return user_info.get("is_admin", False)


def get_user_permissions():
    perm = current_user_perm.get(set())
    return perm


def get_sidebar_items():
    return sidebar_items


def timeago(dt):
    now = datetime.utcnow()
    diff = now - dt

    if diff > timedelta(days=1):
        return None

    seconds = int(diff.total_seconds())
    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"


def score_filter(value):
    try:
        return chr(int(value) + 65)
    except (ValueError, TypeError):
        return "?"


def score_color(value):
    lst = ["green", "yellow", "orange", "red", "maroon"]
    if value is not None and value >= 0 and value < 5:
        return lst[value]
    return "gray"


templates.env.filters["startsWith"] = startsWith
templates.env.filters["findingSeverityMap"] = findingSeverityMap
templates.env.filters["assessmentTypeMap"] = assessmentTypeMap
templates.env.filters["slaCalc"] = slaCalc
templates.env.filters["datetime_format"] = datetime_format
templates.env.filters["score"] = score_filter
templates.env.filters["score_color"] = score_color
templates.env.filters["statusBadgeMap"] = statusBadgeMap

templates.env.globals["is_admin"] = is_admin
templates.env.globals["get_user_info"] = get_current_user
templates.env.globals["get_user_permissions"] = get_user_permissions
templates.env.globals["get_sidebar_items"] = get_sidebar_items
templates.env.globals["now_utc"] = datetime.now(tz=pytz.utc)
templates.env.globals["now"] = datetime.now()
templates.env.filters["timeago"] = timeago
