import polars as pl


def process(file: bytes) -> pl.LazyFrame:
    return pl.scan_csv(file)
