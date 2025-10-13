import polars as pl


def process(file: bytes) -> pl.LazyFrame:
    return (
        pl.scan_csv(file)
        .select(pl.all().name.map(lambda x: "_".join(x.lower().split(" "))))
        .filter(pl.col("risk") != "None")
        .with_columns(
            pl.col("solution", "description", "plugin_output").str.replace_all(
                "\n", " <br/> "
            ),
            pl.lit("Cloud_Assets").alias("host"),
            pl.lit(0).alias("port")
        )
        .rename(
            {
                "solution": "remediation",
                "plugin_output": "evidence",
            }
        )
        .unique(subset=["name", "description", "remediation"])
    )
