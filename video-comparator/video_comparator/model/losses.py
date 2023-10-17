import torch
import torch.nn.functional as F
from torch import nn


class TripletLoss(nn.Module):
    def __init__(self, gamma=1.0):
        super().__init__()
        self.gamma = gamma

    def forward(self, sim_pos, sim_neg):
        loss = F.relu(sim_neg - sim_pos + self.gamma)
        return loss.mean()


class SimilarityRegularizationLoss(nn.Module):
    def __init__(self, lower_limit=-1.0, upper_limit=1.0):
        super().__init__()
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit

    def forward(self, sim):
        loss = torch.sum(torch.abs(torch.clamp(sim - self.lower_limit, max=0.0)))
        loss += torch.sum(torch.abs(torch.clamp(sim - self.upper_limit, min=0.0)))
        return loss
