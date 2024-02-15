import pytest
from core.client.detect_anything import DetectAnythingClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from shapely.geometry import box


def calculate_iou_shapely(bbox1, bbox2):
    # Convert bounding boxes to Shapely boxes
    box1 = box(bbox1[0], bbox1[1], bbox1[2], bbox1[3])
    box2 = box(bbox2[0], bbox2[1], bbox2[2], bbox2[3])

    # Calculate intersection and union
    intersection = box1.intersection(box2).area
    union = box1.union(box2).area

    # Calculate IoU
    iou = intersection / union
    return iou


# pylint: disable=unused-argument
@pytest.mark.parametrize(
    "image_path, bbox, label",
    [
        (
            "gs://datasets-neuronest/label_box_gallery/lipstick.jpeg",
            box(minx=220, miny=240, maxx=310, maxy=680),
            "lipstick",
        ),
    ],
)
def test_endpoint_inference(
    image_path: str,
    bbox,
    label,
    detect_anything_client: DetectAnythingClient,
    uninstantiate_teardown,
):
    image_path = GSPath(image_path)

    StorageClient().download_blob_to_file(
        bucket_name=image_path.bucket,
        source_blob_name=image_path.blob_name,
        destination_file_name=image_path,
    )

    prediction = detect_anything_client.predict_batch(
        images_and_texts_prompts=[(image_path, [label])]
    )[0]

    acceptable_iou = 0.8
    if (
        calculate_iou_shapely(bbox1=bbox, bbox2=prediction.shapely_bbox())
        < acceptable_iou
    ):
        raise RuntimeError(
            f"iOu is too low, < {acceptable_iou}, for tested image {image_path}"
        )
