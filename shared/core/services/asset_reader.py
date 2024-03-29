import logging
from functools import partial
from typing import List, Optional, Tuple, Union

import cv2 as cv
import numpy as np

from core.google.storage_client import StorageClient
from core.path import build_path, build_paths
from core.schemas.asset import AssetType, ImageAsset, VideoAsset, VisualAsset
from core.services.reader_common import (
    infer_asset_type,
    is_path_asset_type_coherent,
    retrieve_asset_locally,
)

logger = logging.getLogger(__name__)


def make_asset(
    asset_path: str,
    asset_type: Optional[AssetType] = None,
    storage_client: Optional[StorageClient] = None,
    time_step: Optional[float] = None,
) -> Union[ImageAsset, VideoAsset]:
    """
    Read an image or a video, encode each frame as binary if specified.

    :param asset_path: The path of the asset to be read. Can be HTTP, GS, or local path.
    :param asset_type: The type of the asset to be read. If set to None, will be
    inferred from the asset path extension.
    :param storage_client: A GCP storage client, only needed if the asset is not stored
    locally.
    :param time_step: The time step between two consecutive sampled frames, which is
    equal to the inverse of the sampled frame rate. Used in the case of video assets
    only.

    :return: An Asset object, containing the frame(s) of the asset along with
    the metadata.
    """
    asset_path = build_path(asset_path)

    if asset_type is None:
        asset_type = infer_asset_type(asset_path)
    else:
        if (
            is_path_asset_type_coherent(asset_path=asset_path, asset_type=asset_type)
            is False
        ):
            raise ValueError(
                f"asset_path not coherent with received asset_type: {asset_type}"
            )

    with retrieve_asset_locally(
        asset_path=asset_path, storage_client=storage_client
    ) as (delete, local_asset_path):
        return asset_type.asset_builder(
            asset_path=local_asset_path, time_step=time_step, delete=delete
        )


def make_assets(
    assets_paths: List[str],
    asset_type: Optional[AssetType] = None,
    storage_client: Optional[StorageClient] = None,
    time_step: Optional[float] = None,
) -> Union[List[ImageAsset], List[VideoAsset]]:
    return [
        make_asset(
            asset_path=asset_path,
            asset_type=asset_type,
            storage_client=storage_client,
            time_step=time_step,
        )
        for asset_path in build_paths(assets_paths)
    ]


def must_be_resized(image: np.ndarray, max_allowed_size: int) -> bool:
    buf = VisualAsset.to_binary(image)
    return len(buf) > max_allowed_size


def resize_image(image: np.ndarray, targeted_dim: Tuple[int, int]) -> np.ndarray:
    if targeted_dim == image.shape[::-1]:
        return image

    return cv.resize(
        image, tuple(np.maximum(targeted_dim, 1)), interpolation=cv.INTER_AREA
    )


def compute_image_buffer_size(
    image: np.ndarray, targeted_dim: Optional[Tuple[int, int]] = None
) -> int:
    if targeted_dim is None:
        return len(VisualAsset.to_binary(image))

    return len(VisualAsset.to_binary(resize_image(image, targeted_dim)))


def get_middle_point(
    interval: Tuple[Tuple[int, int], Tuple[int, int]]
) -> Tuple[int, int]:
    (first_width, first_height), (second_width, second_height) = interval

    return (
        (first_width + second_width) // 2,
        (first_height + second_height) // 2,
    )


def split_interval(
    interval: Tuple[Tuple[int, int], Tuple[int, int]]
) -> Tuple[
    Tuple[Tuple[int, int], Tuple[int, int]], Tuple[Tuple[int, int], Tuple[int, int]]
]:
    (first_width, first_height), (second_width, second_height) = interval
    middle_point = get_middle_point(interval)

    return (
        ((first_width, first_height), middle_point),
        (
            middle_point,
            (second_width, second_height),
        ),
    )


def reduce_image_size_to_binary_target(
    image: np.ndarray,
    max_allowed_image_bytes_quantity: int,
    current_search_interval: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None,
    tolerance: float = 0.01,
) -> np.ndarray:
    if len(image.shape) not in (2, 3):
        raise ValueError(
            f"The received NumPy array doesn't have the expected number of dimensions "
            f"(received {len(image.shape)} dimensions)"
        )

    if image.dtype != np.uint8:
        raise ValueError(
            f"The received NumPy array dtype is not uint8 (received {image.dtype})"
        )

    height, width = image.shape[:2]
    epsilon = max_allowed_image_bytes_quantity * tolerance

    if current_search_interval is None:
        if compute_image_buffer_size(image) < max_allowed_image_bytes_quantity:
            return image

        current_search_interval = (0, 0), (width, height)

    logger.debug(f"current interval: {current_search_interval}")

    resized_image = resize_image(image, get_middle_point(current_search_interval))
    encoded_image_size = compute_image_buffer_size(resized_image)

    lower_left_interval, upper_right_interval = split_interval(current_search_interval)

    if current_search_interval in (lower_left_interval, upper_right_interval):
        return resized_image

    next_iteration_search = partial(
        reduce_image_size_to_binary_target,
        image=image,
        max_allowed_image_bytes_quantity=max_allowed_image_bytes_quantity,
        tolerance=tolerance,
    )

    if encoded_image_size > max_allowed_image_bytes_quantity:
        return next_iteration_search(current_search_interval=lower_left_interval)

    if encoded_image_size < max_allowed_image_bytes_quantity - epsilon:
        return next_iteration_search(current_search_interval=upper_right_interval)

    return resized_image
