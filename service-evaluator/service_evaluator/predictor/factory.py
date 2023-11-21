from __future__ import annotations

import importlib
import inspect
import os
import pkgutil
from typing import Dict, TypeVar

from service_evaluator.predictor.base import PredictorMixin


class ServicePredictorFactory:
    _modules = {
        module_info.name: importlib.import_module(f"{__package__}.{module_info.name}")
        for module_info in pkgutil.iter_modules([os.path.dirname(__file__)])
    }
    _service_predictors: Dict[str, ServicePredictor] = {
        module_name: cls
        for module_name, module in _modules.items()
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if PredictorMixin in cls.__bases__
    }

    @classmethod
    def new(
        cls, service_name: str, service_client_parameters: Dict[str, str]
    ) -> ServicePredictor:
        try:
            service_predictor = cls._service_predictors[service_name]
        except KeyError as key_error:
            raise ValueError(f"Unknown service_name: {service_name}") from key_error

        return service_predictor(service_client_parameters=service_client_parameters)


ServicePredictor = TypeVar("ServicePredictor", bound="PredictorMixin")
