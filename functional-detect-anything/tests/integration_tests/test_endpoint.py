import pytest
from core.client.detect_anything import DetectAnythingClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.schemas.detect_anything import DetectAnythingPredictionBbox
from shapely.geometry import box


def calculate_iou(
    bbox1: DetectAnythingPredictionBbox, bbox2: DetectAnythingPredictionBbox
):
    # Convert bounding boxes to Shapely boxes
    box1 = box(minx=bbox1.min_x, miny=bbox1.min_y, maxx=bbox1.max_x, maxy=bbox1.max_y)
    box2 = box(minx=bbox2.min_x, miny=bbox2.min_y, maxx=bbox2.max_x, maxy=bbox2.max_y)

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
            DetectAnythingPredictionBbox(min_x=220, min_y=550, max_x=310, max_y=680),
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
    print(
        calculate_iou(
            DetectAnythingPredictionBbox(min_x=220, min_y=550, max_x=310, max_y=680),
            DetectAnythingPredictionBbox(min_x=225, min_y=535, max_x=314, max_y=677),
        )
    )
    image_path = GSPath(image_path)

    prediction = detect_anything_client.predict_batch(
        rgb_images_and_texts_prompts=[
            (
                StorageClient().download_blob_as_image(
                    bucket_name=image_path.bucket, blob_name=image_path.blob_name
                ),
                [label],
            )
        ]
    )[0]

    acceptable_iou = 0.75
    if calculate_iou(bbox1=bbox, bbox2=prediction.shapely_bbox()) < acceptable_iou:
        raise RuntimeError(
            f"iOu is too low, < {acceptable_iou}, for tested image {image_path}"
        )
