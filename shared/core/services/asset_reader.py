import logging
import tempfile
from functools import partial
from typing import List, Optional, Tuple, Union

import numpy as np

from core.google.storage_client import StorageClient
from core.path import build_path, build_paths
from core.schemas.asset import (
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    AssetType,
    ImageAsset,
    VideoAsset,
    VisualAsset,
)
from core.services.asset_resizer import resize_image
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
    resized_shape_or_minimal_value: Optional[Union[int, Tuple[int, int]]] = None,
    force_delete_even_if_local: bool = False,
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
    :param resized_shape_or_minimal_value: The targeted shape (height, width) we want
    to have for the image or each frame in case of a video. If a single value in given
    instead, it will be considered as the desired minimum dimension while maintaining
    the aspect ratio.
    :param force_delete_even_if_local: If True, the local file will be removed, even if
    the asset_path is already a local path. It's a destroying action: be sure that your
    asset_path is a temporary file if force_delete_even_if_local is True.

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
            asset_path=local_asset_path,
            time_step=time_step,
            resized_shape_or_minimal_value=resized_shape_or_minimal_value,
            delete=force_delete_even_if_local or delete,
        )


def make_asset_from_bytes(asset: bytes, extension: str, **kwargs):
    if extension not in IMAGE_EXTENSIONS.union(VIDEO_EXTENSIONS):
        raise ValueError(
            f"The received extension is unknown, currently supported extensions: "
            f"{IMAGE_EXTENSIONS.union(VIDEO_EXTENSIONS)}"
        )

    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temporary_file:
        asset_path = temporary_file.name

        with open(asset_path, "wb") as fp:
            fp.write(asset)

    return make_asset(asset_path=asset_path, force_delete_even_if_local=True, **kwargs)


def make_assets(
    assets_paths: List[str],
    asset_type: Optional[AssetType] = None,
    storage_client: Optional[StorageClient] = None,
    time_step: Optional[float] = None,
    resized_shape_or_minimal_value: Optional[Union[int, Tuple[int, int]]] = None,
) -> Union[List[ImageAsset], List[VideoAsset]]:
    return [
        make_asset(
            asset_path=asset_path,
            asset_type=asset_type,
            storage_client=storage_client,
            time_step=time_step,
            resized_shape_or_minimal_value=resized_shape_or_minimal_value,
        )
        for asset_path in build_paths(assets_paths)
    ]


def must_be_resized(image: np.ndarray, max_allowed_size: int) -> bool:
    buf = VisualAsset.frame_to_binary(image)
    return len(buf) > max_allowed_size


def compute_image_buffer_size(
    image: np.ndarray, targeted_dim: Optional[Tuple[int, int]] = None
) -> int:
    if targeted_dim is None:
        return len(VisualAsset.frame_to_binary(image))

    return len(VisualAsset.frame_to_binary(resize_image(image, targeted_dim)))


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

    resized_image = resize_image(image, get_middle_point(current_search_interval)[::-1])
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
