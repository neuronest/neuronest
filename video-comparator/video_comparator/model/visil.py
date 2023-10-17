import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torchvision import models

from video_comparator.model import layers, similarities


class FeatureExtractor(nn.Module):
    def __init__(self, whiteninig=False, dims=3840):
        super().__init__()
        self.normalizer = layers.VideoNormalizer()

        self.cnn = models.resnet50(pretrained=True)

        # self.rpool = layers.RMAC()
        self.layers = {"layer1": 28, "layer2": 14, "layer3": 6, "layer4": 3}
        if whiteninig or dims != 3840:
            self.pca = layers.PCA(dims)

    def extract_region_vectors(self, input_x):
        tensors = []
        # pylint: disable=protected-access
        for name, module in self.cnn._modules.items():
            if name not in {"avgpool", "fc", "classifier"}:
                input_x = module(input_x).contiguous()
                if name in self.layers:
                    # region_vectors = self.rpool(x)
                    layer = self.layers[name]
                    region_vectors = F.max_pool2d(
                        input_x, [layer, layer], int(np.ceil(layer / 2))
                    )
                    region_vectors = F.normalize(region_vectors, p=2, dim=1)
                    tensors.append(region_vectors)
        input_x = torch.cat(tensors, 1)
        input_x = input_x.view(input_x.shape[0], input_x.shape[1], -1).permute(0, 2, 1)
        input_x = F.normalize(input_x, p=2, dim=-1)
        return input_x

    def forward(self, input_x):
        input_x = self.normalizer(input_x)
        input_x = self.extract_region_vectors(input_x)
        if hasattr(self, "pca"):
            input_x = self.pca(input_x)
        return input_x


class ViSiLHead(nn.Module):
    def __init__(
        self, dims=3840, attention=True, video_comperator=True, symmetric=False
    ):
        super().__init__()
        if attention:
            self.attention = layers.Attention(dims, norm=True)
        if video_comperator:
            self.video_comperator = similarities.VideoComperator()
        self.tensor_dot = similarities.TensorDot("biok,bjpk->biopj")
        self.f2f_sim = similarities.ChamferSimilarity(axes=[3, 2], symmetric=symmetric)
        self.v2v_sim = similarities.ChamferSimilarity(axes=[2, 1], symmetric=symmetric)
        self.htanh = nn.Hardtanh()

    def frame_to_frame_similarity(self, query, target):
        sim = self.tensor_dot(query, target)
        return self.f2f_sim(sim)

    def visil_output(self, sim):
        sim = sim.unsqueeze(1)
        return self.video_comperator(sim).squeeze(1)

    def video_to_video_similarity(self, query, target):
        sim = self.frame_to_frame_similarity(query, target)
        if hasattr(self, "video_comperator"):
            sim = self.visil_output(sim)
            sim = self.htanh(sim)
        return self.v2v_sim(sim)

    def attention_weights(self, input_x):
        input_x, weights = self.attention(input_x)
        return input_x, weights

    def prepare_tensor(self, input_x):
        if hasattr(self, "attention"):
            input_x, _ = self.attention_weights(input_x)
        return input_x

    def apply_constrain(self):
        if hasattr(self, "att"):
            self.att.apply_contraint()

    def forward(self, query, target):
        if query.ndim == 3:
            query = query.unsqueeze(0)
        if target.ndim == 3:
            target = target.unsqueeze(0)
        return self.video_to_video_similarity(query, target)


class ViSiL(nn.Module):
    def __init__(
        self,
        pretrained=False,
        dims=3840,
        whiteninig=True,
        attention=True,
        video_comperator=True,
        symmetric=False,
    ):
        super().__init__()

        if pretrained and not symmetric:
            self.cnn = FeatureExtractor(whiteninig=True, dims=3840)
            self.visil_head = ViSiLHead(3840, True, True, False)
            self.visil_head.load_state_dict(
                torch.hub.load_state_dict_from_url("http://ndd.iti.gr/visil/visil.pth")
            )
        elif pretrained and symmetric:
            self.cnn = FeatureExtractor(whiteninig=True, dims=512)
            self.visil_head = ViSiLHead(512, True, True, True)
            self.visil_head.load_state_dict(
                torch.hub.load_state_dict_from_url(
                    "http://ndd.iti.gr/visil/visil_symmetric.pth"
                )
            )
        else:
            self.cnn = FeatureExtractor(whiteninig=whiteninig, dims=dims)
            self.visil_head = ViSiLHead(dims, attention, video_comperator, symmetric)

    def calculate_video_similarity(self, query, target):
        return self.visil_head(query, target)

    def calculate_f2f_matrix(self, query, target):
        return self.visil_head.frame_to_frame_similarity(query, target)

    def calculate_visil_output(self, query, target):
        sim = self.visil_head.frame_to_frame_similarity(query, target)
        return self.visil_head.visil_output(sim)

    def extract_features(self, video_tensor):
        features = self.cnn(video_tensor)
        features = self.visil_head.prepare_tensor(features)
        return features

    def forward(self, input_x):
        raise NotImplementedError(
            "forward method is not implemented, "
            "extract_features and calculate_video_similarity methods are used instead"
        )
