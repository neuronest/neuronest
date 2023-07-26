import torch
import torch.nn.functional as F
from torch import nn


class TensorDot(nn.Module):
    def __init__(self, pattern="iak,jbk->iabj", metric="cosine"):
        super().__init__()
        self.pattern = pattern
        self.metric = metric

    def forward(self, query, target):
        if self.metric == "cosine":
            sim = torch.einsum(self.pattern, [query, target])
        elif self.metric == "euclidean":
            sim = 1 - 2 * torch.einsum(self.pattern, [query, target])
        elif self.metric == "hamming":
            sim = torch.einsum(self.pattern, query, target) / target.shape[-1]
        return sim


class ChamferSimilarity(nn.Module):
    def __init__(self, symmetric=False, axes=None):
        if axes is None:
            axes = [1, 0]
        super().__init__()
        if symmetric:
            self.sim_fun = lambda x: self.symmetric_chamfer_similarity(x, axes=axes)
        else:
            self.sim_fun = lambda x: self.chamfer_similarity(
                x, max_axis=axes[0], mean_axis=axes[1]
            )

    def chamfer_similarity(self, similarity, max_axis=1, mean_axis=0):
        similarity = torch.max(similarity, max_axis, keepdim=True)[0]
        similarity = torch.mean(similarity, mean_axis, keepdim=True)
        return similarity.squeeze(max(max_axis, mean_axis)).squeeze(
            min(max_axis, mean_axis)
        )

    def symmetric_chamfer_similarity(self, similarity, axes=None):
        if axes is None:
            axes = [0, 1]
        return (
            self.chamfer_similarity(similarity, max_axis=axes[0], mean_axis=axes[1])
            + self.chamfer_similarity(similarity, max_axis=axes[1], mean_axis=axes[0])
        ) / 2

    def forward(self, similarity_input):
        return self.sim_fun(similarity_input)


class VideoComperator(nn.Module):  # pylint: disable=too-many-instance-attributes
    def __init__(self):
        super().__init__()
        self.rpad1 = nn.ReplicationPad2d(1)
        self.conv1 = nn.Conv2d(1, 32, 3)
        self.pool1 = nn.MaxPool2d((2, 2), 2)

        self.rpad2 = nn.ReplicationPad2d(1)
        self.conv2 = nn.Conv2d(32, 64, 3)
        self.pool2 = nn.MaxPool2d((2, 2), 2)

        self.rpad3 = nn.ReplicationPad2d(1)
        self.conv3 = nn.Conv2d(64, 128, 3)

        self.fconv = nn.Conv2d(128, 1, 1)

        self.reset_parameters()

    def reset_parameters(self):
        for module in self.modules():
            if isinstance(module, nn.Conv2d):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(self, sim_matrix):
        sim = self.rpad1(sim_matrix)
        sim = F.relu(self.conv1(sim))
        sim = self.pool1(sim)

        sim = self.rpad2(sim)
        sim = F.relu(self.conv2(sim))
        sim = self.pool2(sim)

        sim = self.rpad3(sim)
        sim = F.relu(self.conv3(sim))
        sim = self.fconv(sim)
        return sim
