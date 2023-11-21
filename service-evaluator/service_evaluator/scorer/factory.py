from __future__ import annotations

import importlib
import inspect
import os
import pkgutil
from typing import Dict, TypeVar

from service_evaluator.scorer.base import ScorerMixin


class ServiceScorerFactory:
    _modules = {
        module_info.name: importlib.import_module(f"{__package__}.{module_info.name}")
        for module_info in pkgutil.iter_modules([os.path.dirname(__file__)])
    }
    _service_scorers: Dict[str, ServiceScorer] = {
        module_name: cls
        for module_name, module in _modules.items()
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if ScorerMixin in cls.__bases__
    }

    @classmethod
    def new(cls, service_name: str) -> ServiceScorer:
        try:
            service_predictor = cls._service_scorers[service_name]
        except KeyError as key_error:
            raise ValueError(f"Unknown service_name: {service_name}") from key_error

        return service_predictor()


ServiceScorer = TypeVar("ServiceScorer", bound="ScorerMixin")
