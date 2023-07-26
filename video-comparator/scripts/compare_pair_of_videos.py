import argparse

import torch

from video_comparator.model.visil import ViSiL
from video_comparator.utils import load_video

if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Process two video files.")

    # Add the required arguments
    parser.add_argument("--video1_path", type=str, help="Path to the first video file.")
    parser.add_argument(
        "--video2_path", type=str, help="Path to the second video file."
    )

    # Parse the command line arguments

    args = parser.parse_args()

    # # Load the two videos from the video files
    query_video = torch.from_numpy(load_video(args.video1_path))
    target_video = torch.from_numpy(load_video(args.video2_path))

    # Initialize pretrained ViSiL model
    model = ViSiL(pretrained=True).to("cuda")  # pylint: disable=invalid-name
    model.eval()

    # Extract features of the two videos
    query_features = model.extract_features(query_video.to("cuda"))
    target_features = model.extract_features(target_video.to("cuda"))

    # Calculate similarity between the two videos
    similarity = model.calculate_video_similarity(query_features, target_features)

    print(similarity)
