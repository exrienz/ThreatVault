import json
from urllib import parse

from src.domain.entity.finding import Log


def generate_doughnut_url(log: Log | None, type_: str = "VA"):
    if log is None:
        return None, None
    return _generate_status_chart(log, type_), _generate_severity_chart(log)


def _generate_status_chart(log: Log, type_: str = "VA"):
    colors = ["#FF0000", "#800000", "#008000", "#000000"]
    labels = ["New", "Open", "Closed", "Exemption"]
    if type_ == "HA":
        labels = ["Passed", "Failed", "Warning", "Exemption"]
    values = [getattr(log, f"t{label}") for label in labels]
    return _generate_url(values, colors, labels)


def _generate_severity_chart(log: Log):
    colors = ["#800000", "#FF0000", "#FFA500", "#FFFF00"]
    labels = ["Critical", "High", "Medium", "Low"]
    values = [getattr(log, f"t{label}") for label in labels]
    return _generate_url(values, colors, labels)


def _generate_url(values: list[int], colors: list[str], labels: list[str]):
    dataset = {
        "datasets": [
            {
                "data": values,
                "backgroundColor": colors,
            }
        ],
        "labels": labels,
    }
    config = {
        "type": "doughnut",
        "data": dataset,
        "options": {"plugins": {"datalabels": {"color": "#fff", "fontSize": 15}}},
    }
    base_url = "https://quickchart.io/chart?c="
    return base_url + parse.quote(json.dumps(config))
