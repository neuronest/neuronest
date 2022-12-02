import contextlib
import tempfile
from typing import Optional, Tuple

from neuronest.core.google.storage_client import StorageClient
from neuronest.core.path import GSPath, HTTPPath, LocalPath, Path
from neuronest.core.schemas.asset import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, AssetType
from neuronest.core.tools import extract_file_extension


def infer_asset_type(asset_path: Path) -> AssetType:
    if any(asset_path.endswith(extension) for extension in IMAGE_EXTENSIONS):
        return AssetType.IMAGE

    if any(asset_path.endswith(extension) for extension in VIDEO_EXTENSIONS):
        return AssetType.VIDEO

    raise ValueError(f"Extension of asset path not supported: {asset_path}")


@contextlib.contextmanager
def retrieve_asset_locally(
    asset_path: str, storage_client: Optional[StorageClient]
) -> Tuple[bool, LocalPath]:
    if isinstance(asset_path, (GSPath, HTTPPath)):
        if storage_client is None:
            raise ValueError("A storage client must be passed for cloud located assets")

        with tempfile.NamedTemporaryFile(
            suffix=extract_file_extension(asset_path), delete=False
        ) as temporary_file:
            storage_client.download_blob_to_file(
                *asset_path.to_bucket_and_blob_names(),
                destination_file_name=temporary_file.name,
            )
            local_asset_path = temporary_file.name

        yield True, local_asset_path
        return

    yield False, asset_path
