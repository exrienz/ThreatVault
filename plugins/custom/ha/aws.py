import ast
import io
import re

import pandas as pd


def sanitize_csv_field(field):
    """
    Sanitize CSV field content by removing or escaping problematic characters.
    Ensures fields containing commas are properly quoted.

    Args:
        field: The field content to sanitize

    Returns:
        str: Sanitized field content safe for CSV parsing.
    """
    # Convert to string if not already
    field = str(field)

    # Remove or replace problematic characters
    # Replace newlines and carriage returns with spaces
    field = re.sub(r"[\r\n]+", " ", field)

    # Replace multiple whitespace with single spaces
    field = re.sub(r"\s+", " ", field)

    # Escape double quotes by doubling them (CSV standard)
    field = field.replace('"', '""')

    # Remove or replace other control characters
    field = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", field)

    # Strip leading/trailing whitespace
    field = field.strip()

    # Wrap field in quotes if it contains commas, double quotes, or newlines
    if "," in field or '"' in field or "\n" in field:
        field = f'"{field}"'

    return field


def sanitize_dataframe(df):
    """
    Apply field sanitization to all string columns in a DataFrame.

    Args:
        df: pandas DataFrame to sanitize

    Returns:
        pandas.DataFrame: DataFrame with sanitized string fields
    """
    df_copy = df.copy()

    # Apply sanitization to all object/string columns
    for column in df_copy.columns:
        if df_copy[column].dtype == "object":
            df_copy[column] = df_copy[column].apply(sanitize_csv_field)

    return df_copy


def extract_cve(title):
    match = re.search(r"(CVE-\d{4}-\d{4,7})", title)
    return match.group(1) if match else ""


def clean_title(title):
    return re.sub(r"CVE-\d{4}-\d{4,7}\s*-*\s*", "", title).strip()


def extract_host_from_tags(tag_str, fallback):
    try:
        tag_dict = ast.literal_eval(tag_str)
        for key in [
            "Name",
            "Hostname",
            "FQDN",
            "Application",
            "karpenter.sh/nodepool",
            "karpenter.k8s.aws/ec2nodeclass",
        ]:
            if key in tag_dict:
                return tag_dict[key]
        return fallback
    except:
        return fallback


def process(file: bytes):
    input_file = io.BytesIO(file)
    df = pd.read_csv(input_file)

    df = sanitize_dataframe(df)

    df_filtered = df[df["Product Name"].isin(["Security Hub"])].copy()
    df_filtered.loc[:, "Host"] = df_filtered.apply(
        lambda row: extract_host_from_tags(
            row.get("Resource Tags", "{}"), row["Resource ID"]
        ),
        axis=1,
    )
    return pd.DataFrame(
        {
            "status": df_filtered["Compliance"],
            "host": df_filtered["Host"],
            "port": 0,
            "name": df_filtered["Title"],
            "description": df_filtered["Description"],
            "remediation": df_filtered["Remediation Text"],
            "evidence": df_filtered["Remediation Text"],
            "risk": None,
        }
    )
