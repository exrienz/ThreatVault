import ast

import polars as pl


def process(file: bytes) -> pl.LazyFrame:
    # Load data in lazy mode
    df = pl.scan_csv(file)

    # Normalize headers: lowercase + replace spaces with underscores
    df = df.rename({col: col.lower().replace(" ", "_") for col in df.columns})

    # Filter for Inspector product (equivalent to original VA filter)
    df_filtered = df.filter(pl.col("product_name") == "Inspector")

    # Helper to extract host from tags or fallback to resource_id
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

    # Add host column using the helper logic
    df_filtered = df_filtered.with_columns(
        pl.struct(["resource_tags", "resource_id"])
        .map_elements(
            lambda row: extract_host_from_tags(
                row["resource_tags"], row["resource_id"]
            ),
            return_dtype=pl.String,
        )
        .alias("host")
    )

    # Extract CVE
    df_filtered = df_filtered.with_columns(
        pl.col("title")
        .str.extract(r"(CVE-\d{4}-\d{4,7})", 1)
        .fill_null("")
        .alias("cve")
    )

    # Clean title
    df_filtered = df_filtered.with_columns(
        pl.col("title")
        .str.replace(r"CVE-\d{4}-\d{4,7}\s*-*\s*", "")
        .str.strip()
        .alias("cleaned_title")
    )

    # Clean text fields if they exist
    text_fields = ["solution", "description", "plugin_output"]
    for field in text_fields:
        if field in df_filtered.columns:
            df_filtered = df_filtered.with_columns(
                pl.col(field).str.replace_all("\n", " <br/> ").alias(field)
            )

    # Rename columns
    column_mapping = {
        "solution": "remediation",
        "plugin_output": "evidence",
        "severity": "risk",
        "cleaned_title": "name",
        "remediation_text": "remediation",  # Map remediation_text to remediation
    }

    df_filtered = df_filtered.rename(column_mapping)

    # Enforce schema - VA
    schema = {
        "cve": pl.String,
        "risk": pl.String,
        "host": pl.String,
        "port": pl.Int64,
        "name": pl.String,
        "description": pl.String,
        "remediation": pl.String,
        "evidence": pl.String,
        "vpr_score": pl.String,
    }

    # Ensure all required columns are present with correct dtypes
    for col, dtype in schema.items():
        if col not in df_filtered.columns:
            df_filtered = df_filtered.with_columns(pl.lit("").cast(dtype).alias(col))

    # Cast columns to proper types and keep only schema columns in order
    df_final = df_filtered.select(list(schema.keys())).cast(schema)

    return df_final
