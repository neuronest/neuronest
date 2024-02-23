import os

import cv2
import groundingdino
import requests

# import torch
from groundingdino.util.inference import (  # Model,
    annotate,
    load_and_transform_image_path,
    load_model,
    predict,
)

# from PIL import Image
# from transformers import SamModel, SamProcessor

# device = "cuda" if torch.cuda.is_available() else "cpu"
# model = SamModel.from_pretrained("facebook/sam-vit-huge").to(device)
# processor = SamProcessor.from_pretrained("facebook/sam-vit-huge")
#
# img_url = "https://huggingface.co/ybelkada/segment-anything/resolve/main/assets/car.png"
# raw_image = Image.open(requests.get(img_url, stream=True).raw).convert("RGB")
# input_points = [[[450, 600]]]  # 2D location of a window in the image
#
# import datetime
#
# for _ in range(10):
#     start_time = datetime.datetime.now()
#     inputs = processor(raw_image, input_points=input_points, return_tensors="pt").to(
#         device
#     )
#     with torch.no_grad():
#         outputs = model(**inputs)
#     end_first_instruction = datetime.datetime.now()
#     print(
#         f"Time between the two instructions: ",
#         (end_first_instruction - start_time).total_seconds(),
#     )
# masks = processor.image_processor.post_process_masks(
#     outputs.pred_masks.cpu(),
#     inputs["original_sizes"].cpu(),
#     inputs["reshaped_input_sizes"].cpu(),
# )
#
# scores = outputs.iou_scores
#
# for mask in masks:
#     show_cropped_image(image, mask)


CONFIG_PATH = (
    "Grounded-Segment-Anything/GroundingDINO/groundingdino"
    "/config/GroundingDINO_SwinT_OGC.py"
)
CONFIG_PATH = "./groundingdino/config/GroundingDINO_SwinT_OGC.py"
CHECKPOINT_PATH = os.path.expanduser(
    "~/.cache/neuronest/detect-anything/"
    "github.com_IDEA-Research_GroundingDINO_releases_"
    "download_v0.1.0-alpha_groundingdino_swint_ogc.pth"
)
DEVICE = "cuda"
# IMAGE_PATH = "Grounded-Segment-Anything/assets/demo7.jpg" #
with open("downloaded_image.jpg", "wb") as file:
    file.write(
        requests.get(
            "https://nmaahc.si.edu/sites/default/files/styles/max_1300x1300/public/"
            "images/header/audience-citizen_0.jpg?itok=unjNTfkP",
            timeout=10,
        ).content
    )
IMAGE_PATH = "downloaded_image.jpg"


# TEXT_PROMPT = "Woman. Clouds. Grasses. Sky. Hill."
TEXT_PROMPT = "Woman. Clouds. Grasses. Sky. Hill."
BOX_TRESHOLD = 0.35
TEXT_TRESHOLD = 0.25

image_source, image = load_and_transform_image_path(IMAGE_PATH)

model = load_model(
    model_config_path=os.sep.join(
        [
            os.path.dirname(groundingdino.__file__),
            "config",
            "GroundingDINO_SwinT_OGC.py",
        ]
    ),
    model_checkpoint_path=CHECKPOINT_PATH,
    device="cuda",
)

boxes, logits, phrases = predict(
    model=model,
    image=image,
    caption=TEXT_PROMPT,
    box_threshold=BOX_TRESHOLD,
    text_threshold=TEXT_TRESHOLD,
    device=DEVICE,
)

annotated_frame = annotate(
    image_source=image_source, boxes=boxes, logits=logits, phrases=phrases
)
cv2.imwrite("annotated_image.jpg", annotated_frame)
