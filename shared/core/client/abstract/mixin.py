from abc import ABC, abstractmethod
from typing import Optional, Self

from core.schemas.image_name import ImageNameWithTag


class ClientMixin(ABC):
    MANDATORY_FIELDS = ()
    OPTIONAL_FIELDS = ()

    @classmethod
    def from_primitive_attributes(cls, **kwargs) -> Self:
        for mandatory_field in cls.MANDATORY_FIELDS:
            if mandatory_field not in kwargs:
                raise ValueError(f"The mandatory field '{mandatory_field}' is missing")

        mandatory_values = {
            mandatory_field: kwargs[mandatory_field]
            for mandatory_field in cls.MANDATORY_FIELDS
        }
        optional_values = {
            optional_field: kwargs[optional_field]
            for optional_field in cls.OPTIONAL_FIELDS
            if optional_field in kwargs
        }

        return cls(
            **mandatory_values,
            **optional_values,
        )

    @abstractmethod
    def get_underlying_serving_image(
        self, project_id: str, location: str, key_path: Optional[str] = None
    ) -> ImageNameWithTag:
        raise NotImplementedError
