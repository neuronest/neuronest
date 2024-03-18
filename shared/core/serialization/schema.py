from enum import Enum
from typing import Any, Dict, List, Tuple, Union, get_args, get_origin, get_type_hints

import numpy as np
import pandas as pd
from PIL import Image
from pydantic import BaseModel

from core.path import GSPath
from core.serialization.array import array_from_string, array_to_string
from core.serialization.dataframe import dataframe_from_string, dataframe_to_string


# pylint: disable=too-many-return-statements
def serialize(value: Any):
    if value is None:
        return None
    if isinstance(value, (int, float, str)):
        return value
    if isinstance(value, GSPath):
        return value
    if isinstance(value, np.ndarray):
        return array_to_string(value)
    if isinstance(value, Image.Image):
        return array_to_string(np.array(value))
    if isinstance(value, pd.DataFrame):
        return dataframe_to_string(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [serialize(field_value_element) for field_value_element in value]
    if isinstance(value, tuple):
        return tuple(serialize(field_value_element) for field_value_element in value)
    if isinstance(value, Schema):
        return value.serialized_attributes_dict()

    raise NotImplementedError


def typing_is_optional(typing) -> bool:
    # example: get_origin(Union[float, None]) == Union
    # other example: get_origin(Optional[float]) == Union
    if get_origin(typing) is not Union:
        return False
    typings_in_union = get_args(typing)
    if len(typings_in_union) != 2:
        return False
    _, expected_none_type = typings_in_union
    if expected_none_type is not None.__class__:
        return False

    return True


# pylint: disable=too-many-return-statements
def deserialize_normal_class(normal_class, value: Any):
    if value is None:
        return None
    if normal_class in (int, float, str, bool):
        return value
    if issubclass(normal_class, Enum):
        return value
    if normal_class is GSPath:
        return GSPath(value)
    if normal_class is np.ndarray:
        return array_from_string(value)
    if normal_class is pd.DataFrame:
        return dataframe_from_string(value)
    if normal_class is Image.Image:
        return Image.fromarray(array_from_string(value))

    # for example get_origin(List[str]) == list, get_origin(int) == None
    # container_typing = get_origin(class_or_container_typing)
    if issubclass(normal_class, Schema):
        return normal_class.from_serialized_attributes_dict(value)

    raise TypeError(f"{normal_class} is  not an allowed class")


def deserialize_container_typing(container_typing, value: Any):
    container_typing_origin = get_origin(container_typing)
    # value_container_class is not None here
    if typing_is_optional(typing=container_typing):
        # example: get_args(Optional[str]) == (str,)
        return deserialize_normal_class_or_container_typing(
            normal_class_or_container_typing=get_args(container_typing)[0], value=value
        )
    if container_typing_origin is Union:
        raise TypeError(
            "Union typing not allowed as it prevents automatic determination "
            "of which class to deserialize"
        )

    if container_typing_origin in (List, list):
        return [
            deserialize_normal_class_or_container_typing(
                normal_class_or_container_typing=get_args(container_typing)[0],
                value=value_element,
            )
            for value_element in value
        ]
    if container_typing_origin in (Tuple, tuple):
        return tuple(
            deserialize_normal_class_or_container_typing(
                normal_class_or_container_typing=contained_typing,
                value=value_element,
            )
            for value_element, contained_typing in zip(
                value, get_args(container_typing)
            )
        )

    raise TypeError(f"Unmanaged container typing: {container_typing.__name__}")


def is_a_container_typing(anything: Any) -> bool:
    return get_origin(anything) is not None


def deserialize_normal_class_or_container_typing(
    normal_class_or_container_typing, value
):
    if is_a_container_typing(normal_class_or_container_typing):
        return deserialize_container_typing(normal_class_or_container_typing, value)

    return deserialize_normal_class(normal_class_or_container_typing, value)


class Schema(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    def serialized_attributes_dict(self) -> Dict[str, Any]:
        serialized_attributes_dict = {}
        for field_name in self.__fields__:
            field_value = getattr(self, field_name)

            if field_value is None:
                serialized_attributes_dict[field_name] = None
            elif isinstance(field_value, Schema):
                serialized_attributes_dict[
                    field_name
                ] = field_value.serialized_attributes_dict()
            else:
                serialized_attributes_dict[field_name] = serialize(value=field_value)

        return serialized_attributes_dict

    @classmethod
    def from_serialized_attributes_dict(
        cls, serialized_attributes_dict: Dict[str, Any]
    ) -> "Schema":
        deserialized_attributes_dict = {}
        for key, value in serialized_attributes_dict.items():
            value_class = get_type_hints(cls)[key]

            if value is None:
                deserialized_attributes_dict[key] = None
            # if is a generic type from typing module or a class other than Schema
            elif get_origin(value_class) is not None or not issubclass(
                value_class, Schema
            ):
                deserialized_attributes_dict[
                    key
                ] = deserialize_normal_class_or_container_typing(
                    normal_class_or_container_typing=value_class, value=value
                )
            else:
                # is a class inherited from Schema
                deserialized_attributes_dict[
                    key
                ] = value_class.from_serialized_attributes_dict(value)

        return cls(**deserialized_attributes_dict)
