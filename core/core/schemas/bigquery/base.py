import json
from abc import ABC
from datetime import datetime
from typing import List
from uuid import uuid4

from google.cloud import bigquery
from pydantic import BaseModel, Field, root_validator

from neuronest.core.path import GSPath
from neuronest.core.schemas.environment import Environment

BIG_QUERY_TYPES_MAPPING = {
    str: bigquery.enums.SqlTypeNames.STRING,
    int: bigquery.enums.SqlTypeNames.INTEGER,
    float: bigquery.enums.SqlTypeNames.FLOAT,
    datetime: bigquery.enums.SqlTypeNames.DATETIME,
    GSPath: bigquery.enums.SqlTypeNames.STRING,
    Environment: bigquery.enums.SqlTypeNames.STRING,
}


class BigQueryModel(ABC, BaseModel):
    __tablename__ = ""
    __bigquery_tablename__ = ""
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    created_date: datetime
    updated_date: datetime

    def dict(self, **kwargs):
        """Override BaseModel dict method to serialize datetime and dict fields"""
        output = super().dict(**kwargs)
        for key, value in output.items():
            if isinstance(value, datetime):
                output[key] = value.isoformat()

            if isinstance(value, dict):
                output[key] = json.dumps(value)

        return output

    @root_validator(pre=True)
    # pylint: disable=no-self-argument
    def populate_datetimes(cls, values: dict) -> dict:
        date_now = datetime.now()

        values["created_date"] = values.get("created_date") or date_now
        values["updated_date"] = values.get("updated_date") or date_now

        return values

    @classmethod
    def to_big_query_fields(cls) -> List[bigquery.SchemaField]:
        return [
            bigquery.SchemaField(
                name=model_field_name,
                field_type=BIG_QUERY_TYPES_MAPPING.get(model_field.type_)
                or bigquery.enums.SqlTypeNames.STRING,
                mode="REQUIRED"
                if model_field.required is True
                or model_field.default_factory is not None
                or model_field.default is not None
                else "NULLABLE",
            )
            for model_field_name, model_field in cls.__fields__.items()
        ]
