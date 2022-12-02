import datetime
import json
import logging
import os
import tempfile
import time
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from cv2 import cv2 as cv
from google.api_core.exceptions import Conflict, NotFound
from google.cloud import storage
from google.cloud.storage import Bucket
from tqdm import tqdm

from neuronest.core.exceptions import DependencyError
from neuronest.core.path import GSPath
from neuronest.core.serialization.encoding import NumpyEncoder

logger = logging.getLogger(__name__)


class StorageClient:
    def __init__(self, key_path: Optional[str] = None):
        self.client = (
            storage.Client()
            if not key_path
            else storage.Client.from_service_account_json(key_path)
        )

    @staticmethod
    def generate_gs_link(bucket_name: str, blob_name: str) -> GSPath:
        return GSPath(os.path.join("gs://", bucket_name, blob_name))

    @staticmethod
    def safe_load_json(content: bytes) -> dict:
        try:
            deserialized_content = json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError) as loading_exception:
            logger.error("The blob found could not be JSON deserialized")
            raise DependencyError from loading_exception
        return deserialized_content

    def create_bucket(self, bucket_name: str, location: str, exist_ok: bool = False):
        try:
            self.client.create_bucket(bucket_name, location=location)
        except Conflict as exception:
            if not exist_ok:
                raise exception

    def upload_blob(self, source_file_name: str, bucket_name: str, blob_name: str):
        """
        Upload a file to a bucket.

        :param source_file_name: A filename stored locally.
        :param bucket_name: The bucket name.
        :param blob_name: The blob name.
        """
        bucket = self.client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(source_file_name)

        logger.info(
            f"File {source_file_name} uploaded to the bucket '{bucket_name}' "
            f"as {blob_name}."
        )

    def upload_blob_from_bytes(self, bucket_name: str, blob_name: str, content: bytes):
        """
        Upload a string to a bucket as a plain text file.

        :param bucket_name: The bucket name.
        :param blob_name: The blob name.
        :param content: A binary content.
        """
        bucket = self.client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content, content_type="application/octet-stream")

        logger.info(f"Bytes uploaded to the bucket '{bucket_name}' as {blob_name}.")

    def upload_blob_from_string(self, bucket_name: str, blob_name: str, content: str):
        """
        Upload a string to a bucket as a plain text file.

        :param bucket_name: The bucket name.
        :param blob_name: The blob name.
        :param content: A content string.
        """
        bucket = self.client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content)

        logger.info(f"String uploaded to the bucket '{bucket_name}' as {blob_name}.")

    def upload_blob_from_dict(self, bucket_name: str, blob_name: str, content: dict):
        """
        Upload a dictionary to a bucket as a JSON file.

        :param bucket_name: The bucket name.
        :param blob_name: The blob name.
        :param content: A content dictionary.
        """
        extension = ".json"
        bucket = self.client.get_bucket(bucket_name)

        if not blob_name.endswith(extension):
            blob_name += extension

        blob = bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(content, cls=NumpyEncoder, ensure_ascii=False, indent=4),
            content_type="application/json",
        )

        logger.info(
            f"Dictionary uploaded to the bucket '{bucket_name}' as {blob_name}."
        )

    def upload_blob_from_dataframe(
        self, bucket_name: str, blob_name: str, content: pd.DataFrame
    ):
        """
        Upload a Pandas DataFrame to a bucket as a CSV file.

        :param bucket_name: The bucket name.
        :param blob_name: The blob name.
        :param content: A content DataFrame.
        """
        extension = ".csv"

        if not blob_name.endswith(extension):
            blob_name += extension

        with tempfile.NamedTemporaryFile(suffix=extension) as named_temporary_file:
            content.to_csv(named_temporary_file.name, index=False)
            self.upload_blob(
                bucket_name=bucket_name,
                source_file_name=named_temporary_file.name,
                blob_name=blob_name,
            )

        logger.info(f"DataFrame uploaded to the bucket '{bucket_name}' as {blob_name}.")

    def copy_blob(
        self,
        source_bucket_name: str,
        source_blob_name: str,
        destination_bucket_name: str,
        destination_blob_name: str,
    ):
        source_bucket = self.client.get_bucket(source_bucket_name)
        source_blob = source_bucket.blob(source_blob_name)
        destination_bucket = self.client.get_bucket(destination_bucket_name)
        destination_blob = destination_bucket.blob(destination_blob_name)

        # Note: source_bucket.copy_blob method seems to fail when to blob size is too
        # big. See below:
        # https://objectpartners.com/2021/01/19/rewriting-files-in-google-cloud-storage/
        # Instead, we are looping over the blob rewrite method.

        try:
            rewrite_token = False
            while True:
                (
                    rewrite_token,
                    _,
                    _,
                ) = destination_blob.rewrite(source_blob, token=rewrite_token)
                if not rewrite_token:
                    break
        except NotFound as not_found:
            message = (
                f"The blob {source_blob_name} has not been found in the bucket "
                f"{source_bucket}, or the destination bucket {destination_bucket}"
                f"does not exist"
            )
            logger.info(message)
            raise DependencyError(message) from not_found

    def download_blob_to_file(
        self, bucket_name: str, source_blob_name: str, destination_file_name: str
    ):
        """
        Download a blob from a bucket and store it locally.

        :param bucket_name: The bucket name.
        :param source_blob_name: The source blob name.
        :param destination_file_name: The local destination file.
        """
        os.makedirs(os.path.dirname(destination_file_name), exist_ok=True)
        bucket: Bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        try:
            blob.download_to_filename(destination_file_name)
        except NotFound as not_found:
            message = (
                f"The blob {source_blob_name} has not been found in the bucket "
                f"{bucket_name}"
            )
            logger.info(message)
            raise DependencyError(message) from not_found

        logger.info(
            f"The blob {source_blob_name} has been downloaded to "
            f"{destination_file_name}"
        )

    def download_blob(
        self, bucket_name: str, blob_name: str, as_json: bool = False
    ) -> Union[dict, bytes]:
        """
        Download a blob from a bucket and retrieve its content.

        :param bucket_name: The bucket name.
        :param blob_name: The source blob name.
        :param as_json: Whether to consider to retrieved blob as JSON. If applicable,
        it will be casted as dictionary.

        :return: The blob found content as binary or dictionary.
        """
        bucket: Bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        try:
            content = blob.download_as_bytes()
        except NotFound as not_found:
            message = (
                f"The blob {blob_name} has not been found in the bucket "
                f"{bucket_name}"
            )
            logger.info(message)
            raise DependencyError(message) from not_found

        if as_json:
            return self.safe_load_json(content)

        return content

    def download_blob_as_image(self, bucket_name: str, blob_name: str) -> np.ndarray:
        """
        Download a blob from a bucket and convert it to an NumPy array image.

        :param bucket_name: The bucket name.
        :param blob_name: The source blob name.

        :return: The blob found content as NumPy array image.
        """
        raw_image = self.download_blob(bucket_name, blob_name)
        image = cv.imdecode(np.frombuffer(raw_image, np.uint8), cv.IMREAD_UNCHANGED)

        if image is None:
            message = (
                f"The blob {blob_name} in the bucket {bucket_name} could not be loaded "
                f"as an image"
            )
            logger.info(message)
            raise DependencyError(message)

        return image

    # pylint: disable=too-many-locals
    def download_multiple_blobs(
        self,
        bucket_name: str,
        prefix: str = "",
        suffix: Optional[str] = None,
        excluded_names: Tuple[str, ...] = tuple(),
        as_json: bool = False,
        include_document_names: bool = False,
        verbose: bool = True,
    ) -> Union[List[Union[dict, bytes]], Dict[str, Union[dict, bytes]]]:
        """
        Retrieve and download multiple blobs having a specific prefix, if specified.

        If the prefix is not specified, download every blob in the bucket.

        :param bucket_name: The bucket name.
        :param prefix: Prefix of the blobs to be downloaded.
        :param suffix: The optional suffix of the blob to search. If specified,
        the matching blobs will be filtered to keep only those ending with the suffix.
        :param excluded_names: Tuple of blob names to be excluded.
        :param as_json: Whether to consider the retrieved blobs as JSON. If applicable,
        they will be cast as dictionary.
        :param include_document_names: Whether to also return the documents ids as keys.
        If it is so, a dictionary is returned instead of a list.
        :param verbose: Whether to show to progress bar during downloading.

        :return: The content of the blobs found, as a list of binaries or dictionaries.
        """
        # from an arbitrary number beyond which it becomes difficult to log it
        printable_prefix = (
            prefix if len(prefix) <= 20 else prefix[:10] + "[...]" + prefix[-10:]
        )

        blobs = list(self.client.list_blobs(bucket_name, prefix=prefix))

        if len(blobs) == 0:
            logger.info(
                f"No blob found in {bucket_name} with the prefix "
                f"'{printable_prefix}'"
            )
            return {} if include_document_names else []

        logger.info(
            f"{len(blobs)} blob in '{bucket_name}' with the prefix "
            f"'{printable_prefix}' has been found"
        )

        blobs = [
            blob
            for blob in blobs
            if (suffix is None or blob.name.endswith(suffix))
            and os.path.basename(blob.name) not in excluded_names
        ]

        if len(blobs) == 0:
            logger.info(
                f"No blob found in '{bucket_name}' with the prefix "
                f"'{printable_prefix}' and the suffix '{suffix}'"
            )
            return {} if include_document_names else []

        document_names, contents = [], []

        if verbose:
            blobs = tqdm(blobs)

        for blob in blobs:
            if os.path.basename(blob.name) in excluded_names:
                continue

            try:
                content = blob.download_as_bytes()
            except NotFound:
                logger.warning(f"Blob {blob.name} not found, retrying..")
                time.sleep(1)
                blob = storage.Blob(bucket=Bucket(bucket_name), name=blob.name)

                try:
                    content = blob.download_as_bytes()
                except NotFound as not_found:
                    message = (
                        f"The blob '{blob.name}' has not been found in the bucket "
                        f"'{bucket_name}'"
                    )
                    logger.info(message)
                    raise DependencyError(message) from not_found

            if len(content) == 0:
                continue

            document_names.append(blob.name)

            if as_json:
                contents.append(self.safe_load_json(content))
            else:
                contents.append(content)

        if include_document_names:
            return dict(zip(document_names, contents))

        return contents

    def download_last_blob_with_prefix(
        self,
        bucket_name: str,
        prefix: str,
        suffix: Optional[str] = None,
        excluded_names: Tuple[str, ...] = tuple(),
        max_days_age: Optional[int] = None,
        as_json: bool = False,
    ) -> Optional[Union[dict, bytes]]:
        """
        Retrieve and download the most recent blob for a given prefix
        (i.e. sub-directory).

        :param bucket_name: The bucket name to search in.
        :param prefix: The prefix of the blob to search. If multiple matches exist, the
        most recent one will be kept.
        :param suffix: The optional suffix of the blob to search. If specified,
        the matching blobs will be filtered to keep only those ending with the suffix.
        :param excluded_names: Tuple of blob names to be excluded.
        :param max_days_age: The highest blob number of days authorized.
        :param as_json: Whether to consider the retrieved blob as JSON. If applicable,
        it will be cast as dictionary.

        :return: The blob found content as binary or dictionary.
        """
        # from an arbitrary number beyond which it becomes difficult to log it
        printable_prefix = (
            prefix if len(prefix) <= 20 else prefix[:10] + "[...]" + prefix[-10:]
        )

        blobs = list(self.client.list_blobs(bucket_name, prefix=prefix))

        if len(blobs) == 0:
            logger.info(
                f"No blob found in '{bucket_name}' with the prefix "
                f"'{printable_prefix}'"
            )
            return None

        blobs = [
            blob
            for blob in blobs
            if (suffix is None or blob.name.endswith(suffix))
            and os.path.basename(blob.name) not in excluded_names
        ]

        if len(blobs) == 0:
            logger.info(
                f"No blob found in '{bucket_name}' with the prefix "
                f"'{printable_prefix}' and the suffix '{suffix}'"
            )
            return None

        last_blob = sorted(blobs, key=lambda blob: blob.time_created, reverse=True)[0]
        if max_days_age is not None:
            delta = (
                datetime.datetime.now(last_blob.time_created.tzinfo)
                - last_blob.time_created
            )
            if delta.days > max_days_age:
                logger.info(
                    f"The blob found in '{bucket_name}' with the prefix "
                    f"'{printable_prefix}' is too old and is thus discarded "
                    f"({delta.days} days for a maximum of {max_days_age} days)"
                )
                return None

        logger.info(
            f"A blob in '{bucket_name}' with the prefix '{printable_prefix}' has been "
            f"found"
        )

        content = last_blob.download_as_bytes()

        if as_json:
            return self.safe_load_json(content)

        return content

    def delete_blob(self, bucket_name: str, blob_name: str):
        """
        Delete a specific blob.

        :param bucket_name: The bucket name.
        :param blob_name: The blob name.
        """
        bucket: Bucket = self.client.bucket(bucket_name)
        try:
            bucket.delete_blob(blob_name)
        except NotFound as not_found:
            message = (
                f"The blob '{blob_name}' has not been found in the bucket "
                f"'{bucket_name}'"
            )
            logger.info(message)
            raise DependencyError(message) from not_found

        logger.info(f"The blob '{blob_name}' has been deleted from '{bucket_name}'")

    def delete_multiple_blobs(self, bucket_name: str, prefix: Optional[str] = None):
        """
        Delete multiple blobs having a specific prefix, if specified.

        If the prefix is not specified, delete every blob in the bucket.

        :param bucket_name: The bucket name.
        :param prefix: Prefix of the blobs to be deleted.
        """
        bucket: Bucket = self.client.bucket(bucket_name)
        try:
            bucket.delete_blobs(blobs=list(bucket.list_blobs(prefix=prefix)))
        except NotFound as not_found:
            message = (
                f"The blobs with prefix '{prefix}' have not been found in the bucket "
                f"'{bucket_name}'"
            )
            logger.error(message)
            raise DependencyError(message) from not_found
