import importlib.util
import logging
import pathlib
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from types import ModuleType
from uuid import UUID

import pandas as pd
import polars as pl
import pytz
from fastapi import UploadFile
from sqlalchemy import Date, cast, delete, func, select, update
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects._typing import (
    _OnConflictConstraintT,
    _OnConflictIndexElementsT,
    _OnConflictIndexWhereT,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exception.error import InvalidInput
from src.application.schemas.finding import FindingUploadSchema
from src.domain.constant import (
    FnStatusEnum,
    HAStatusEnum,
    PluginFunction,
    SeverityEnum,
    VAStatusEnum,
)
from src.domain.entity import CVE, Finding, FindingName
from src.domain.entity.finding import Plugin
from src.domain.entity.project_management import Environment, Product, Project
from src.infrastructure.database import sync_engine
from src.persistence.finding_revert import FindingRevertRepository

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


def insert_conflict_do_nothing(table, conn, keys, data_iter):
    data = [dict(zip(keys, row)) for row in data_iter]
    stmt = insert(table.table).values(data).on_conflict_do_nothing()
    result = conn.execute(stmt)
    return result.rowcount


def compile_query(query):
    compiler = (
        query.compile if not hasattr(query, "statement") else query.statement.compile
    )
    return compiler(dialect=postgresql.dialect())


def insert_conflict_do_update(
    constraint: _OnConflictConstraintT | None = None,
    idx_element: _OnConflictIndexElementsT | None = None,
    idx_where: _OnConflictIndexWhereT | None = None,
    no_update_cols: list | None = None,
    update_dict: dict | None = None,
):
    if no_update_cols is None:
        no_update_cols = []

    if update_dict is None:
        update_dict = {}

    def inner(table, conn, keys, data_iter):
        data = [dict(zip(keys, row)) for row in data_iter]
        stmt = insert(table.table).values(data)
        table_cols = table.frame.columns.values
        update_cols = [c for c in table_cols if c not in no_update_cols]
        update_conflict_data = {
            k: update_dict.get(k, getattr(stmt.excluded, k)) for k in update_cols
        }
        stmt = stmt.on_conflict_do_update(
            constraint=constraint,
            index_elements=idx_element,
            index_where=idx_where,
            set_=update_conflict_data,
        )
        result = conn.execute(stmt)
        return result.rowcount

    return inner


class FileUploadService(ABC):
    def __init__(
        self,
        session: AsyncSession,
        file: UploadFile,
        product_id: UUID,
        data: FindingUploadSchema,
    ):
        self.session: AsyncSession = session
        self.file = file
        self.plugin_id = data.plugin
        self.scan_date = data.scan_date.replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.utc
        )
        self.product_id = product_id
        self.finding_lf: pl.LazyFrame = pl.LazyFrame()
        self.finding_name_lf: pl.LazyFrame = pl.LazyFrame()
        self.process_new_finding = data.process_new_finding
        self.overwrite = data.overwrite
        self.plugin: PluginFunction | ModuleType | None = None

    async def scan_date_validation(self):
        future_date = self.scan_date > datetime.now(tz=pytz.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if future_date:
            raise InvalidInput("Finding date cannot be future date")
        stmt = (
            select(Finding.last_update)
            .where(
                Finding.last_update > self.scan_date,
                Finding.product_id == self.product_id,
            )
            .order_by(Finding.last_update.desc())
        )
        query = await self.session.execute(stmt)
        res = query.scalars().first()
        if res is not None:
            raise InvalidInput(
                f"Finding date must be greater than {res.strftime('%d-%m-%Y')}"
            )

    async def file_validation(self):
        if self.file.content_type is None or self.file.filename is None:
            raise InvalidInput("Invalid file. File metadata seems missing")

        file_type = self.file.content_type.split("/")[-1]
        if file_type != "csv":
            raise InvalidInput("Invalid file type. Currently we only support (csv)")

    async def get_plugin(self):
        stmt = select(Plugin).where(Plugin.id == self.plugin_id)
        query = await self.session.execute(stmt)
        plugin = query.scalars().first()
        if plugin is None:
            raise
        self.plugin = self.plugin_import(
            plugin.name, f"{plugin.type}/{plugin.env}/{plugin.name}.py"
        )
        return self.plugin

    async def run_plugin(self) -> pl.LazyFrame:
        csv_file = await self.file.read()
        if self.plugin is None:
            self.plugin = await self.get_plugin()

        lf = self.plugin.process(csv_file)
        if isinstance(lf, pl.DataFrame):
            lf = lf.lazy()
        if isinstance(lf, pd.DataFrame):
            lf = pl.from_pandas(lf).lazy()
        self.finding_lf = lf
        return self.finding_lf

    async def remove_uploaded_new_finding(self):
        """
        Remove new finding where the self.scan_date is the same.
        This allow user to overwrite uploaded finding for the same date.
        """
        if not self.overwrite:
            return
        stmt = delete(Finding).where(Finding.finding_date == self.scan_date)
        await self.session.execute(stmt)
        await self.session.commit()

    # Deprecated
    async def finding_revert_point(self):
        await FindingRevertRepository.create_revert_point(self.session, self.product_id)

    def plugin_import(self, name: str, filename: str) -> ModuleType:
        ph = pathlib.Path(__file__).cwd()
        path = f"{ph}/public/plugins/{filename}"
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise
        loader = importlib.util.LazyLoader(spec.loader)
        spec.loader = loader
        module = importlib.util.module_from_spec(spec)
        if module is None:
            raise
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    async def finding_name_process(self):
        """
        Add finding name into the database.

        Since, we store finding_name and finding in separate table, we need to update
        the findingName table first since we need it's id to match with the finding
        table.
        """
        self.finding_name_lf = (
            self.finding_lf.select(pl.col("name"), pl.col("description"))
            .group_by(pl.col("name"))
            .agg(pl.first("description"))
        )
        total = self.finding_name_lf.collect().write_database(
            table_name=FindingName.__tablename__,
            connection=sync_engine,
            if_table_exists="append",
            engine_options={"method": insert_conflict_do_nothing},
        )
        logger.info(f"Added {total} new finding names")

    @abstractmethod
    async def upload(self):
        pass

    @abstractmethod
    async def plugin_verification(self):
        pass


class VAUploadService(FileUploadService):
    async def new_finding_check(self):
        """
        Compare database findings against uploaded data.
        Include/Exclude New Finding
        """
        if self.process_new_finding:
            return
        query = (
            select(Finding.port, Finding.host, FindingName.name)
            .join(FindingName)
            .where(Finding.product_id == self.product_id)
        )
        df = pl.read_database(query, connection=sync_engine).lazy()
        fmt_expression = (
            pl.col("host", "name").cast(pl.String),
            pl.col("port").cast(pl.Int64),
        )
        df = df.select(fmt_expression)
        self.finding_lf = self.finding_lf.with_columns(fmt_expression)
        self.finding_lf = self.finding_lf.join(
            df, on=["host", "port", "name"], how="right"
        )

    async def cve_process(self):
        fn_names = self.finding_name_lf.select(pl.col("name")).collect()["name"]
        fn_stmt = select(FindingName.id, FindingName.name).where(
            FindingName.name.in_(fn_names)
        )
        finding_name_lf = pl.read_database(fn_stmt, connection=sync_engine).lazy()

        if finding_name_lf.collect().is_empty():
            return

        q = self.finding_lf.join(finding_name_lf, on="name", how="left").rename(
            {"id": "finding_name_id"}
        )

        q = (
            q.filter(pl.col("cve").is_not_null())
            .group_by(pl.col("cve").alias("name"), pl.col("finding_name_id"))
            .agg(pl.first("risk").str.to_uppercase().alias("severity"))
            .with_columns(pl.col("severity").cast(SeverityEnum))
        )

        total = q.collect().write_database(
            table_name=CVE.__tablename__,
            connection=sync_engine,
            if_table_exists="append",
            engine_options={"method": insert_conflict_do_nothing},
        )
        print(f"Added {total} new CVEs")

    async def final_preprocess(self):
        """
        CSV - DB Mapping
        """
        fn_names = self.finding_name_lf.select(pl.col("name")).collect()["name"]
        fn_stmt = select(FindingName.id, FindingName.name).where(
            FindingName.name.in_(fn_names)
        )
        finding_name_lf = pl.read_database(fn_stmt, connection=sync_engine).lazy()

        self.finding_lf = self.finding_lf.join(
            finding_name_lf, on="name", how="left"
        ).rename({"id": "finding_name_id"})
        self.finding_lf = self.finding_lf.with_columns(
            status=pl.lit(VAStatusEnum.NEW.value),
            severity=pl.col("risk").str.to_uppercase().cast(SeverityEnum),
            finding_date=pl.lit(self.scan_date),
            last_update=pl.lit(self.scan_date),
            plugin_id=pl.lit(self.plugin_id),
            product_id=pl.lit(str(self.product_id)),
        )

        self.finding_lf = self.finding_lf.select(
            pl.exclude("cve", "risk", "name", "description")
        )
        self.finding_lf = self.finding_lf.unique(
            subset=["finding_name_id", "port", "host"]
        )

    async def process(self):
        """
        For the finding upload, we use UPSERT technique.

        ON Conflict (finding_name_id, host, port) already exists for the product,
        we update the "status" with open, the other based on the file itself.
        If there's any other things to update, add it to the update_dict.
        """
        total = self.finding_lf.collect().write_database(
            table_name=Finding.__tablename__,
            connection=sync_engine,
            if_table_exists="append",
            engine_options={
                "method": insert_conflict_do_update(
                    idx_element=(
                        "finding_name_id",
                        "host",
                        "port",
                        "plugin_id",
                        "product_id",
                    ),
                    idx_where=(Finding.status != VAStatusEnum.CLOSED.value),
                    no_update_cols=["finding_date", "finding_name_id"],
                    update_dict={"status": VAStatusEnum.OPEN.value},
                )
            },
        )

        print(f"Processed {total} Findings")

    async def update_new_finding_status(self):
        stmt = (
            update(Finding)
            .where(
                Finding.finding_date == Finding.last_update,
                Finding.status.not_in(
                    [VAStatusEnum.NEW.value, VAStatusEnum.CLOSED.value]
                ),
                Finding.product_id == self.product_id,
            )
            .values(status=VAStatusEnum.NEW.value)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def close_finding(self):
        stmt = (
            update(Finding)
            .where(
                Finding.last_update < self.scan_date,
                Finding.status != VAStatusEnum.CLOSED.value,
                Finding.plugin_id == self.plugin_id,
                Finding.product_id == self.product_id,
            )
            .values(
                status=VAStatusEnum.CLOSED.value,
                last_update=self.scan_date,
                closed_at=self.scan_date,
                closing_effort=func.extract(
                    "day", (self.scan_date - Finding.finding_date)
                ),
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def reopen_finding(self):
        subquery_max = (
            select(
                Finding.finding_name_id,
                Finding.host,
                Finding.port,
                func.max(Finding.finding_date).label("latest_date"),
                func.min(Finding.finding_date).label("first_discovered_date"),
            )
            .group_by(Finding.finding_name_id, Finding.host, Finding.port)
            .having(func.count(Finding.id) > 1)
            .subquery()
        )

        stmt_new = (
            update(Finding)
            .where(
                Finding.finding_name_id == subquery_max.c.finding_name_id,
                Finding.host == subquery_max.c.host,
                Finding.port == subquery_max.c.port,
                Finding.finding_date == subquery_max.c.latest_date,
                Finding.plugin_id == self.plugin_id,
                Finding.product_id == self.product_id,
            )
            .values(
                internal_remark=(
                    func.concat(
                        "The finding is reopened on ",
                        cast(Finding.finding_date, Date),
                        " after first discovered on ",
                        cast(subquery_max.c.first_discovered_date, Date),
                    )
                )
            )
        )

        stmt_old = (
            update(Finding)
            .where(
                Finding.finding_name_id == subquery_max.c.finding_name_id,
                Finding.host == subquery_max.c.host,
                Finding.port == subquery_max.c.port,
                Finding.finding_date == subquery_max.c.first_discovered_date,
                Finding.status == FnStatusEnum.CLOSED.value,
                Finding.plugin_id == self.plugin_id,
                Finding.product_id == self.product_id,
            )
            .values(reopen=True)
        )
        await self.session.execute(stmt_new)
        await self.session.execute(stmt_old)
        await self.session.commit()

    async def upload(self):
        await self.scan_date_validation()
        await self.plugin_verification()
        await self.new_finding_check()
        await self.finding_name_process()
        await self.remove_uploaded_new_finding()
        if not self.finding_name_lf.collect().is_empty():
            await self.cve_process()
            await self.final_preprocess()
        await self.process()
        await self.update_new_finding_status()
        await self.close_finding()
        await self.reopen_finding()

    async def plugin_verification(self):
        await self.file_validation()
        await self.run_plugin()
        df_schema = pl.Schema(
            {
                "cve": pl.String(),
                "risk": pl.String(),
                "host": pl.String(),
                "port": pl.Int64(),
                "name": pl.String(),
                "description": pl.String(),
                "remediation": pl.String(),
                "evidence": pl.String(),
                "vpr_score": pl.String(),
            }
        )

        lf_schema = self.finding_lf.collect_schema()
        if not sorted(lf_schema.items()) == sorted(df_schema.items()):
            raise InvalidInput("Plugin didn't match the file uploaded!")


class HAUploadService(FileUploadService):
    async def passed_finding(self):
        stmt = (
            update(Finding)
            .where(
                Finding.last_update < self.scan_date,
                Finding.status != HAStatusEnum.PASSED.value,
                Finding.plugin_id == self.plugin_id,
                Finding.product_id == self.product_id,
            )
            .values(
                status=HAStatusEnum.PASSED.value,
                last_update=self.scan_date,
                closed_at=self.scan_date,
                closing_effort=func.extract(
                    "day", (self.scan_date - Finding.finding_date)
                ),
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def process(self):
        """
        For the finding upload, we use UPSERT technique.

        ON Conflict (finding_name_id, host, port) already exists for the product,
        we update it with information in the file.
        If there's any other things to update, add it to the update_dict.
        """
        total = self.finding_lf.collect().write_database(
            table_name=Finding.__tablename__,
            connection=sync_engine,
            if_table_exists="append",
            engine_options={
                "method": insert_conflict_do_update(
                    idx_element=(
                        "finding_name_id",
                        "host",
                        "port",
                        "plugin_id",
                        "product_id",
                    ),
                    idx_where=(Finding.status != HAStatusEnum.PASSED.value),
                    no_update_cols=["finding_date", "finding_name_id"],
                )
            },
        )

        print(f"Processed {total} Findings")

    async def additional_preprocess(self):
        self.finding_lf = self.finding_lf.with_columns(
            name=pl.col("name").str.replace_all('"', "")
        )

    async def preprocess(self):
        """
        CSV - DB Mapping
        """
        self.finding_lf = self.finding_lf.with_columns(
            severity=pl.col("risk").fill_null(SeverityEnum.MEDIUM.value),
            evidence=pl.col("evidence").fill_null(""),
        )
        fn_names = self.finding_name_lf.select(pl.col("name")).collect()["name"]
        fn_stmt = select(FindingName.id, FindingName.name).where(
            FindingName.name.in_(fn_names)
        )
        finding_name_lf = pl.read_database(fn_stmt, connection=sync_engine).lazy()

        self.finding_lf = self.finding_lf.join(
            finding_name_lf, on="name", how="left"
        ).rename({"id": "finding_name_id"})
        self.finding_lf = self.finding_lf.with_columns(
            finding_date=pl.lit(self.scan_date),
            last_update=pl.lit(self.scan_date),
            plugin_id=pl.lit(self.plugin_id),
            product_id=pl.lit(str(self.product_id)),
        )

        self.finding_lf = self.finding_lf.select(
            pl.exclude("risk", "name", "description")
        )
        self.finding_lf = self.finding_lf.unique(
            subset=["finding_name_id", "port", "host"]
        )

    async def plugin_verification(self):
        await self.file_validation()
        await self.run_plugin()
        self.finding_lf = self.finding_lf.rename(lambda col: col.lower())
        df_schema = pl.Schema(
            {
                "risk": pl.String(),
                "host": pl.String(),
                "port": pl.Int64(),
                "name": pl.String(),
                "description": pl.String(),
                "remediation": pl.String(),
                "evidence": pl.String(),
                "status": pl.String(),
            }
        )
        lf_schema = self.finding_lf.collect_schema()
        if not sorted(lf_schema.items()) == sorted(df_schema.items()):
            raise InvalidInput("Plugin didn't match the file uploaded!")

    async def upload(self):
        await self.scan_date_validation()
        await self.plugin_verification()
        await self.additional_preprocess()
        await self.finding_name_process()
        await self.remove_uploaded_new_finding()
        await self.preprocess()
        await self.process()
        await self.passed_finding()


class UploadFileServiceGeneral:
    def __init__(
        self,
        session: AsyncSession,
        file: UploadFile,
        product_id: UUID,
        data: FindingUploadSchema,
    ):
        self.session = session
        self.file = file
        self.product_id = product_id
        self.data = data

    async def upload(self) -> FileUploadService:
        stmt = (
            select(Project.type_)
            .join(Environment)
            .join(Product)
            .where(Product.id == self.product_id)
        )
        query = await self.session.execute(stmt)
        project_type = query.scalar_one()
        if project_type == "HA":
            uploader = HAUploadService(
                self.session, self.file, self.product_id, self.data
            )
        else:
            uploader = VAUploadService(
                self.session, self.file, self.product_id, self.data
            )
        try:
            await uploader.upload()
        except pl.exceptions.PolarsError:
            raise InvalidInput("Plugin didn't match the file uploaded!")
        return uploader
