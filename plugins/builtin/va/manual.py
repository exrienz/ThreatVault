# Accepted File: csv,json,xml
import polars as pl


def process(file: bytes, file_type: str) -> pl.LazyFrame:
    return pl.scan_csv(file)
