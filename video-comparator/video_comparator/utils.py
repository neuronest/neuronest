from typing import Union

import cv2
import numpy as np
import torch


def center_crop(frame, desired_size):
    if frame.ndim == 3:
        old_size = frame.shape[:2]
        top = int(np.maximum(0, (old_size[0] - desired_size) / 2))
        left = int(np.maximum(0, (old_size[1] - desired_size) / 2))
        return frame[top : top + desired_size, left : left + desired_size, :]

    old_size = frame.shape[1:3]
    top = int(np.maximum(0, (old_size[0] - desired_size) / 2))
    left = int(np.maximum(0, (old_size[1] - desired_size) / 2))
    return frame[:, top : top + desired_size, left : left + desired_size, :]


def resize_frame(frame, desired_size):
    min_size = np.min(frame.shape[:2])
    ratio = desired_size / min_size
    frame = cv2.resize(
        frame, dsize=(0, 0), fx=ratio, fy=ratio, interpolation=cv2.INTER_CUBIC
    )
    return frame


def load_video(video, all_frames=False, fps=1, cc_size=224, rs_size=256):
    cv2.setNumThreads(1)
    cap = cv2.VideoCapture(video)
    fps_div = fps
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps > 144 or fps is None:
        fps = 25
    frames = []
    count = 0
    while cap.isOpened():
        if int(count % round(fps / fps_div)) == 0 or all_frames:
            # _, frame = cap.retrieve()
            _, frame = cap.read()
            if isinstance(frame, np.ndarray):
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if rs_size is not None:
                    frame = resize_frame(frame, rs_size)
                frames.append(frame)
            else:
                break
        count += 1
    cap.release()
    frames = np.array(frames)
    if cc_size is not None:
        frames = center_crop(frames, cc_size)
    return frames


@torch.no_grad()
def calculate_similarities_to_queries(
    model, queries, target, batch_sz_sim: int = 2048, device: Union[int, str] = None
):
    similarities = []
    for _, query in enumerate(queries):
        if query.device.type == "cpu":
            if device is not None:
                query = query.to(device)
        sim = []
        for batch_index in range(target.shape[0] // batch_sz_sim + 1):
            batch = target[
                batch_index * batch_sz_sim : (batch_index + 1) * batch_sz_sim
            ]
            if batch.shape[0] >= 4:
                sim.append(model.calculate_video_similarity(query, batch))
        sim = torch.mean(torch.cat(sim, 0))
        similarities.append(sim.cpu().numpy())
    return similarities


@torch.no_grad()
def extract_features(
    model, frames, batch_sz: int = 128, device: Union[int, str] = None
):
    features = []
    for i in range(frames.shape[0] // batch_sz + 1):
        batch = frames[i * batch_sz : (i + 1) * batch_sz]
        if batch.shape[0] > 0:
            if device is not None:
                batch = batch.to(device).float()
            features.append(model.extract_features(batch))
    features = torch.cat(features, 0)
    while features.shape[0] < 4:
        features = torch.cat([features, features], 0)
    return features
