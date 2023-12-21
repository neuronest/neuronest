from __future__ import annotations

import os

import pandas as pd
from core.schemas.bigquery.tables import ScoringDataset
from core.schemas.service_evaluator import DatasetName, EvaluatedServiceName
from dvc.config import RemoteNotFoundError
from dvc.exceptions import NoOutputOrStageError
from dvc.repo import Repo
from omegaconf import OmegaConf


class DatasetManager:
    def __init__(
        self,
        dataset_name: DatasetName,
        datasets_directory_name: str,
        dataset_filename: str,
        paths_column: str = "path",
    ):
        self.dataset_name = dataset_name
        self.datasets_directory_name = datasets_directory_name
        self.dataset_filename = dataset_filename
        self.paths_column = paths_column
        self.dataset_path = self._build_dataset_path()
        self.dataset = self._load_dataset()
        self.scoring_dataset = self._build_scoring_dataset()

    @property
    def asset_paths(self) -> pd.Series:
        return self.dataset[self.paths_column].map(
            lambda path: os.path.join(self.dataset_path, path)
        )

    @classmethod
    def from_service_name(
        cls,
        service_name: EvaluatedServiceName,
        datasets_directory_name: str,
        dataset_filename: str,
    ) -> DatasetManager:
        return DatasetManager(
            dataset_name=DatasetName.from_service_name(service_name=service_name),
            datasets_directory_name=datasets_directory_name,
            dataset_filename=dataset_filename,
        )

    def _build_dataset_path(self) -> str:
        return os.path.join(self.datasets_directory_name, self.dataset_name)

    def _check_dataset(self, dataset: pd.DataFrame) -> pd.DataFrame:
        if self.paths_column not in dataset.columns:
            raise ValueError(
                f"The dataset should contain the following column: "
                f"'{self.paths_column}'"
            )

        for path in dataset[self.paths_column]:
            full_path = os.path.join(self.dataset_path, path)
            if not os.path.exists(full_path):
                raise FileNotFoundError(
                    f"The following asset could not be found: '{full_path}'"
                )

        return dataset

    def _load_dataset(self, sep: str = ",") -> pd.DataFrame:
        return self._check_dataset(
            pd.read_csv(os.path.join(self.dataset_path, self.dataset_filename), sep=sep)
        )

    def _build_scoring_dataset(self) -> ScoringDataset:
        dvc_config = OmegaConf.load(self.dataset_path + ".dvc")

        if (outs_number := len(dvc_config.outs)) != 1:
            raise ValueError(
                f"Incorrect dvc file for dataset '{self.dataset_name}' "
                f"(unexpected number of outputs: {outs_number})"
            )

        dvc_config_out = dvc_config.outs[0]
        md5, size, nfiles = (
            dvc_config_out.md5,
            dvc_config_out.size,
            dvc_config_out.nfiles,
        )

        return ScoringDataset(
            path=self.dataset_path,
            name=self.dataset_name,
            md5=md5,
            size=size,
            nfiles=nfiles,
        )

    def pull_dataset(
        self,
        root_directory: str = ".",
    ):
        repo = Repo(root_directory)
        try:
            # noinspection PyCallingNonCallable
            repo.pull(
                targets=[self.dataset_path],
                remote=self.dataset_name,
            )
        except (NoOutputOrStageError, RemoteNotFoundError) as exception:
            raise RuntimeError(
                f"Failed to retrieve the requested dataset name: {self.dataset_name}"
            ) from exception
