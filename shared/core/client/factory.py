from __future__ import annotations

import importlib
import inspect
import os
import pkgutil
from abc import ABC
from typing import Dict, TypeVar

from core.client.base import ClientMixin


class ServiceClientFactory:
    _modules = {
        module_info.name: importlib.import_module(f"{__package__}.{module_info.name}")
        for module_info in pkgutil.iter_modules([os.path.dirname(__file__)])
    }
    _service_clients: Dict[str, ServiceClient] = {
        module_name: cls
        for module_name, module in _modules.items()
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if ClientMixin in inspect.getmro(cls) and ABC not in cls.__bases__
    }

    @classmethod
    def new(cls, service_name: str, **kwargs) -> ServiceClient:
        try:
            service_client = cls._service_clients[service_name]
        except KeyError as key_error:
            raise ValueError(f"Unknown service_name: {service_name}") from key_error

        inspected_parameters = inspect.signature(service_client.__init__).parameters
        service_client_parameters = set(inspected_parameters) - {"self"}
        if not set(service_client_parameters).issubset(kwargs):
            not_present_parameters = service_client_parameters.difference(kwargs)

            if any(
                inspected_parameters[not_present_parameter].default
                is inspect.Parameter.empty
                for not_present_parameter in not_present_parameters
            ):
                raise RuntimeError(
                    f"At least one parameter is missing : "
                    f"{', '.join(not_present_parameters)}"
                )

        parameters = {
            parameter_name: parameter_value
            for parameter_name, parameter_value in kwargs.items()
            if parameter_name in service_client_parameters
        }

        return service_client.from_primitive_attributes(**parameters)


ServiceClient = TypeVar("ServiceClient", bound="ClientMixin")
