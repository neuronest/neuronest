from __future__ import annotations

import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, Union


class RegistryDomain(str, Enum):
    ARTIFACT_REGISTRY_DOMAIN = "{region}-docker.pkg.dev"
    CONTAINER_REGISTRY_DOMAIN = "eu.gcr.io"


class StringWithValidation(ABC, str):
    @classmethod
    @abstractmethod
    def is_valid(cls, name: str) -> bool:
        raise NotImplementedError

    def __new__(cls, name, *args, **kwargs):
        if not cls.is_valid(name):
            raise ValueError(f"Incorrect given name: '{name}'")

        return str.__new__(cls, name, *args, **kwargs)


class PartImageName(StringWithValidation):
    @classmethod
    def is_valid(cls, name: str) -> bool:
        return len(name) > 0 and all(sep not in name for sep in (":", "/"))


class BaseImageName(PartImageName):
    """
    Example: 'people-counting'
    """


class Tag(PartImageName):
    """
    Examples:
        '565726992'
        'f92caee9107a288aa535166334e599e69b0d87119e8d0d147b66877e8f1d3890'
    """

    @classmethod
    def is_valid(cls, name: str) -> bool:
        # sha256 type image identifier and workflow identifier tags are allowed
        regex = r"(^latest$|^[0-9a-z]+$)"

        return super().is_valid(name) and bool(re.fullmatch(regex, name))


class BaseImageNameWithTag(StringWithValidation):
    """
    Example: 'people-counting:565726992'
    """

    @classmethod
    def is_valid(cls, name: str) -> bool:
        base_image_name, tag = cls.split_tag(name)

        return BaseImageName.is_valid(base_image_name) and Tag.is_valid(tag)

    @classmethod
    def split_tag(cls, name: str) -> Tuple[BaseImageName, Tag]:
        base_image_name, tag = name.split(":")

        return BaseImageName(base_image_name), Tag(tag)


class GenericImageName(StringWithValidation):
    @classmethod
    def _split(
        cls, image_name: str
    ) -> Tuple[str, str, str, Union[BaseImageName, BaseImageNameWithTag]]:
        split_image_name = image_name.split("/")

        if len(split_image_name) != 4:
            raise ValueError(f"Wrong image name: {image_name}")

        (
            registry_domain,
            project_id,
            repository_id,
            base_image_name,
        ) = split_image_name

        base_image_name = (
            BaseImageName(base_image_name)
            if BaseImageName.is_valid(base_image_name)
            else BaseImageNameWithTag(base_image_name)
        )

        return (
            registry_domain,
            project_id,
            repository_id,
            base_image_name,
        )

    @classmethod
    def is_valid(cls, name: str) -> bool:
        try:
            cls._split(name)
        except ValueError:
            return False

        return True

    @classmethod
    def build_registry_domain(
        cls, registry_domain: Union[RegistryDomain, str], region: str
    ) -> RegistryDomain:
        return RegistryDomain(registry_domain).format(region=region)

    @classmethod
    def build(
        cls,
        registry_domain: RegistryDomain,
        project_id: str,
        region: str,
        repository_id: str,
        base_image_name: BaseImageName,
        **kwargs,
    ) -> ImageName:
        raise NotImplementedError


class ImageName(GenericImageName):
    TEMPLATE = "{registry_domain}/{project_id}/{repository_id}/{base_image_name}"

    @classmethod
    def _split(cls, image_name: str) -> Tuple[str, str, str, BaseImageName]:
        (
            registry_domain,
            project_id,
            repository_id,
            base_image_name,
        ) = super()._split(image_name)

        return registry_domain, project_id, repository_id, base_image_name

    @classmethod
    def build(
        cls,
        registry_domain: RegistryDomain,
        project_id: str,
        region: str,
        repository_id: str,
        base_image_name: BaseImageName,
        **kwargs,
    ) -> ImageName:
        return cls(
            cls.TEMPLATE.format(
                registry_domain=cls.build_registry_domain(
                    registry_domain=registry_domain, region=region
                ),
                project_id=project_id,
                repository_id=repository_id,
                base_image_name=BaseImageName(base_image_name),
            )
        )


class ImageNameWithTag(GenericImageName):
    TEMPLATE = "{registry_domain}/{project_id}/{repository_id}/{base_image_name}:{tag}"

    @classmethod
    def _split(cls, image_name: str) -> Tuple[str, str, str, BaseImageName, Tag]:
        (
            registry_domain,
            project_id,
            repository_id,
            base_image_name_with_tag,
        ) = super()._split(image_name)

        base_image_name, tag = BaseImageNameWithTag.split_tag(base_image_name_with_tag)

        return (
            registry_domain,
            project_id,
            repository_id,
            base_image_name,
            tag,
        )

    @classmethod
    def build(
        cls,
        registry_domain: RegistryDomain,
        project_id: str,
        region: str,
        repository_id: str,
        base_image_name: BaseImageName,
        **kwargs,
    ) -> ImageNameWithTag:
        return cls(
            cls.TEMPLATE.format(
                registry_domain=cls.build_registry_domain(
                    registry_domain=registry_domain, region=region
                ),
                project_id=project_id,
                repository_id=repository_id,
                base_image_name=BaseImageName(base_image_name),
                tag=Tag(kwargs["tag"]),
            )
        )
