import argparse
from typing import Union

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from video_comparator.datasets.generators import DatasetGenerator
from video_comparator.model.visil import ViSiL


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


def query_vs_target(model, query_target_dataset, args):
    # Create a video generator for the queries
    loader = DataLoader(
        DatasetGenerator(
            args.video_dir, query_target_dataset.get_queries(), args.pattern
        ),
        num_workers=args.workers,
    )

    # Extract features of the queries
    all_db, queries, queries_ids = set(), [], []
    print("> Extract features of the query videos")
    for video in tqdm(loader):
        frames = video[0][0]
        video_id = video[1][0]
        if frames.shape[0] > 0:
            features = extract_features(model, frames, args)
            if not args.load_queries:
                features = features.cpu()
            all_db.add(video_id)
            queries.append(features)
            queries_ids.append(video_id)

    # Create a video generator for the database video
    loader = DataLoader(
        DatasetGenerator(
            args.video_dir, query_target_dataset.get_database(), args.pattern
        ),
        num_workers=args.workers,
    )

    # Calculate similarities between the queries and the database videos
    similarities = {query: {} for query in queries_ids}
    print("\n> Calculate query-target similarities")
    for video in tqdm(loader):
        frames = video[0][0]
        video_id = video[1][0]
        if frames.shape[0] > 0:
            features = extract_features(model, frames, args)
            sims = calculate_similarities_to_queries(model, queries, features, args)
            all_db.add(video_id)
            for i, similarity in enumerate(sims):
                similarities[queries_ids[i]][video_id] = float(similarity)

    print(f"\n> Evaluation on {query_target_dataset.name}")
    query_target_dataset.evaluate(similarities, all_db)


if __name__ == "__main__":

    def get_formatter_class(prog):
        return argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=80)

    # formatter = lambda prog: argparse.ArgumentDefaultsHelpFormatter(
    #     prog, max_help_position=80
    # )
    formatter = get_formatter_class
    parser = argparse.ArgumentParser(
        description="This is the code for the evaluation of ViSiL network on five datasets.",
        formatter_class=formatter,
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        choices=["FIVR-200K", "FIVR-5K", "CC_WEB_VIDEO", "SVD", "EVVE"],
        help="Name of evaluation dataset.",
    )
    parser.add_argument(
        "--video_dir",
        type=str,
        required=True,
        help="Path to file that contains the database videos",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        required=True,
        help='Pattern that the videos are stored in the video directory, eg. "{id}/video.*" '
        'where the "{id}" is replaced with the video Id. Also, it supports '
        "Unix style pathname pattern expansion.",
    )
    parser.add_argument(
        "--batch_sz",
        type=int,
        default=128,
        help="Number of frames contained in each batch during feature extraction.",
    )
    parser.add_argument(
        "--batch_sz_sim",
        type=int,
        default=2048,
        help="Number of feature tensors in each batch during similarity calculation.",
    )
    parser.add_argument("--gpu_id", type=int, default=0, help="Id of the GPU used.")
    parser.add_argument(
        "--load_queries",
        action="store_true",
        help="Flag that indicates that the queries will be loaded to the GPU memory.",
    )
    parser.add_argument(
        "--similarity_function",
        type=str,
        default="chamfer",
        choices=["chamfer", "symmetric_chamfer"],
        help="Function that will be used to calculate similarity "
        "between query-target frames and videos.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of workers used for video loading.",
    )
    parser_args = parser.parse_args()

    if "CC_WEB" in parser_args.dataset:
        from video_comparator.datasets import CC_WEB_VIDEO

        dataset = CC_WEB_VIDEO()
    elif "FIVR" in parser_args.dataset:
        from video_comparator.datasets import FIVR

        dataset = FIVR(version=parser_args.dataset.split("-")[1].lower())
    elif "EVVE" in parser_args.dataset:
        from video_comparator.datasets import EVVE

        dataset = EVVE()
    elif "SVD" in parser_args.dataset:
        from video_comparator.datasets import SVD

        dataset = SVD()
    else:
        raise ValueError(f"Proper dataset name is missing: {parser_args.dataset}")

    visil = ViSiL(  # pylint: disable=invalid-name
        pretrained=True, symmetric="symmetric" in parser_args.similarity_function
    ).to(parser_args.gpu_id)

    visil.eval()

    query_vs_target(visil, dataset, parser_args)
