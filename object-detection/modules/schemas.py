from typing import Dict, List, Optional, Union

from pydantic import BaseModel, validator


class InputSampleSchema(BaseModel):
    data: str
    labels_to_predict: Optional[List[str]] = None
    confidence_threshold: Optional[float] = None
    overridden_image_width: Optional[int] = None

    @property
    def metadata(
        self,
    ) -> Dict[str, Union[Optional[List[str]], Optional[float], Optional[int]]]:
        return {
            "labels_to_predict": self.labels_to_predict,
            "confidence_threshold": self.confidence_threshold,
            "overridden_image_width": self.overridden_image_width,
        }

    @property
    def metadata_filtered(self) -> Dict[str, Union[List[str], float, int]]:
        return {
            metadata_name: metadata_value
            for metadata_name, metadata_value in self.metadata.items()
            if metadata_value is not None
        }


class InputSchema(BaseModel):
    samples: List[InputSampleSchema]

    @validator("samples")
    # pylint: disable=no-self-argument
    def validate_metadata_batch_unicity(
        cls, samples: List[InputSampleSchema]
    ) -> List[InputSampleSchema]:
        if len(samples) == 0:
            return []

        first_sample = samples[0]
        first_sample_metadata_filtered = first_sample.metadata_filtered

        error_message = (
            "If some metadata is specified for one sample, it has to be "
            "equally specified for every samples"
        )

        if len(first_sample_metadata_filtered) == 0:
            if any(len(sample.metadata_filtered) > 0 for sample in samples):
                raise ValueError(error_message)

            return samples

        if any(
            sample.metadata_filtered != first_sample_metadata_filtered
            for sample in samples
        ):
            raise ValueError(error_message)

        return samples


class OutputSchema(BaseModel):
    results: str
