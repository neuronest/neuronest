from typing import List, Tuple, Union

from core.client.abstract.online_prediction_model import OnlinePredictionModelClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.schemas.video_comparator import (
    InputSchema,
    InputSchemaSample,
    OutputSchemaSample,
    PredictionType,
)
from core.tools import get_file_id_from_path


class VideoComparatorClient(OnlinePredictionModelClient):
    # PREPROCESSING_IMAGE_TYPE = ".jpg"
    # MAX_SIZE = (640, 640)
    # MAX_BYTES = 1.5e6
    VIDEOS_TO_COMPARE_BASE_BUCKET_NAME = "vc-videos-to-compare"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage_client = StorageClient(
            key_path=self.key_path, project_id=self.project_id
        )

    # def _create_endpoint(self) -> Optional[requests.Response]:
    #     return self.model_instantiator_client.instantiate(self.model_name)

    # @ttl_cache(ttl=600)
    # def _try_get_endpoint(self) -> aiplatform.Endpoint:
    #     total_waited_time = 0
    #
    #     while total_waited_time < self.endpoint_retry_timeout:
    #         endpoint = self.vertex_ai_manager.get_endpoint_by_name(self.model_name)
    #         # model as described is the registry model that has the largest version_id.
    #         # If the endpoint is well deployed, but with a model that is not that of
    #         # the largest version id, the function does not return the endpoint and
    #         # does an instantiate, which does not make sense in a "_try_get_endpoint"
    #         # function which should just return the deployed endpoint
    #         # the logic could be replaced by this block, which returns the endpoint
    #         # if it is deployed
    #
    #         # def endpoint_is_deployed(endpoint: aiplatform.Endpoint) -> bool:
    #         #     try:
    #         #         endpoint_gca_resource: proto.Message = endpoint.gca_resource
    #         #     except RuntimeError:
    #         #         return False
    #         #     return len(list(endpoint_gca_resource.deployed_models)) >= 1
    #
    #         model = self.vertex_ai_manager.get_model_by_name(
    #             self.model_name, version_aliases=("default",)
    #         )
    #
    #         if endpoint is not None and self.vertex_ai_manager.is_model_deployed(
    #             model=model, endpoint=endpoint
    #         ):
    #             return endpoint
    #
    #         self._create_endpoint()
    #         time.sleep(self.endpoint_retry_wait_time)
    #         total_waited_time += self.endpoint_retry_wait_time
    #
    #     raise DependencyError(
    #         f"Failed to deploy an endpoint for model_name={self.model_name}, "
    #         f"giving up after {self.endpoint_retry_timeout // 60} minutes of trying"
    #     )

    # @staticmethod
    # def _are_shapes_correct(images: List[np.ndarray]) -> bool:
    #     if any(
    #         image.ndim not in (2, 3) or image.ndim == 3 and image.shape[2] != 3
    #         for image in images
    #     ):
    #         return False
    #
    #     return True

    # def _resize_images(self, images: List[np.ndarray]) -> List[np.ndarray]:
    #     """
    #     If any dimension of an image if greater than self.MAX_SIZE (width, height),
    #     then the image is going to be resized without changing the ratio,
    #     with self.MAX_SIZE being the maximum.
    #     """
    #     return [
    #         resize(
    #             image=image,
    #             height=self.MAX_SIZE[0]
    #             if image.shape[0] > self.MAX_SIZE[0] and image.shape[0] > image.shape[1]
    #             else None,
    #             width=self.MAX_SIZE[1]
    #             if image.shape[1] > self.MAX_SIZE[1] and image.shape[1] > image.shape[0]
    #             else None,
    #         )
    #         for image in images
    #     ]

    # def _split_into_chunks(
    #     self, preprocessed_images: List[Dict[str, str]]
    # ) -> List[List[Dict[str, str]]]:
    #     if len(preprocessed_images) == 0:
    #         return []
    #
    #     if len(preprocessed_images) == 1:
    #         return [preprocessed_images]
    #
    #     if (
    #         sum(
    #             len(preprocessed_image["data"])
    #             for preprocessed_image in preprocessed_images
    #         )
    #         <= self.MAX_BYTES
    #     ):
    #         return [preprocessed_images]
    #
    #     for index, preprocessed_image in enumerate(preprocessed_images):
    #         if (image_bytes := len(preprocessed_image["data"])) > self.MAX_BYTES:
    #             raise ValueError(
    #                 f"Cannot proceed, image at index {index} is too large: "
    #                 f"{image_bytes/1e6}MB"
    #             )
    #
    #     chunks, bytes_current_chunk = [[preprocessed_images[0]]], len(
    #         preprocessed_images[0]["data"]
    #     )
    #     for preprocessed_image in preprocessed_images[1:]:
    #         bytes_current_image = len(preprocessed_image["data"])
    #         if bytes_current_image + bytes_current_chunk <= self.MAX_BYTES:
    #             chunks[-1].append(preprocessed_image)
    #             bytes_current_chunk += bytes_current_image
    #             continue
    #
    #         chunks.append([preprocessed_image])
    #         bytes_current_chunk = bytes_current_image
    #
    #     return chunks

    @property
    def videos_to_compare_bucket(self) -> str:
        return f"{self.VIDEOS_TO_COMPARE_BASE_BUCKET_NAME}-{self.project_id}"

    def _upload_video_to_storage(self, video_path: str) -> GSPath:
        bucket = self.storage_client.client.bucket(self.videos_to_compare_bucket)

        if not bucket.exists():
            bucket.create()

        video_blob_name = get_file_id_from_path(file_path=video_path)

        self.storage_client.upload_blob(
            source_file_name=video_path,
            bucket_name=bucket.name,
            blob_name=video_blob_name,
        )

        return GSPath.from_bucket_and_blob_names(
            bucket_name=bucket.name, blob_name=video_blob_name
        )

    # pylint: disable=arguments-renamed
    def predict_batch(
        self,
        video_path_pairs: List[Tuple[str, str]],
        prediction_type: PredictionType = PredictionType.SIMILARITY,
    ) -> Union[List[float], List[List[float]]]:
        """
        video_path_pairs: List of pairs of videos paths
        """
        # list of str --> input paths output embeddings
        # list of tuples --> input paths or embeddings output similarities
        # if list of str:
        #     video_paths = data
        # elif list of tuples:
        #     video_path_pairs = data
        # else:
        #     raise ValueError("")

        endpoint = self._try_get_endpoint()

        gs_video_path_pairs = [
            (
                self._upload_video_to_storage(video_path=video_path),
                self._upload_video_to_storage(video_path=other_video_path),
            )
            for video_path, other_video_path in video_path_pairs
        ]
        return [
            OutputSchemaSample.parse_obj(sample_prediction).results
            for sample_prediction in endpoint.predict(
                InputSchema(
                    samples=[
                        InputSchemaSample(
                            video_path=gs_video_path,
                            other_video_path=gs_other_video_path,
                            prediction_type=prediction_type,
                        )
                        for gs_video_path, gs_other_video_path in gs_video_path_pairs
                    ]
                ).dict()["samples"]
            ).predictions
        ]
        #
        # if not self._are_shapes_correct(images):
        #     raise ValueError("Incorrect received shapes")
        #
        # preprocessed_images = [
        #     {
        #         "data": image_to_string(
        #             frame=image,
        #             extension=self.PREPROCESSING_IMAGE_TYPE,
        #         )
        #     }
        #     for image in self._resize_images(images=images)
        # ]
        # chunks_preprocessed_images = self._split_into_chunks(preprocessed_images)

        # endpoint = self._try_get_endpoint()
        # raw_chunked_predictions = [
        #     endpoint.predict(chunk_preprocessed_images).predictions
        #     for chunk_preprocessed_images in chunks_preprocessed_images
        # ]
        # predictions = [
        #     array_from_string(OutputSchema.parse_obj(raw_prediction).results)
        #     for raw_predictions in raw_chunked_predictions
        #     for raw_prediction in raw_predictions
        # ]
        #
        # return [
        #     pd.DataFrame(prediction, columns=PREDICTION_COLUMNS)
        #     for prediction in predictions
        # ]

    #
    # def predict_single(self, image: np.ndarray) -> pd.DataFrame:
    #     """
    #     images: A RGB image as NumPy array
    #     """
    #     return self.predict_batch([image])[0]
