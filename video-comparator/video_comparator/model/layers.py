import torch
import torch.nn.functional as F
from torch import nn


class VideoNormalizer(nn.Module):
    def __init__(self):
        super().__init__()
        self.scale = nn.Parameter(torch.Tensor([255.0]), requires_grad=False)
        self.mean = nn.Parameter(
            torch.Tensor([0.485, 0.456, 0.406]), requires_grad=False
        )
        self.std = nn.Parameter(
            torch.Tensor([0.229, 0.224, 0.225]), requires_grad=False
        )

    def forward(self, video):
        video = ((video / self.scale) - self.mean) / self.std
        return video.permute(0, 3, 1, 2)


# class RMAC(nn.Module):
#     def __init__(self, L=[3]):
#         super(RMAC, self).__init__()
#         self.L = L
#
#     def forward(self, x):
#         return self.region_pooling(x, L=self.L)
#
#     def region_pooling(self, x, L=[3]):
#         ovr = 0.4  # desired overlap of neighboring regions
#         steps = torch.Tensor(
#             [2, 3, 4, 5, 6, 7]
#         )  # possible regions for the long dimension
#
#         W = x.shape[3]
#         H = x.shape[2]
#
#         w = min(W, H)
#         # w2 = math.floor(w / 2.0 - 1)
#
#         b = (max(H, W) - w) / (steps - 1)
#         (tmp, idx) = torch.min(
#             torch.abs(((w**2 - w * b) / w**2) - ovr), 0
#         )  # steps(idx) regions for long dimension
#
#         # region overplus per dimension
#         Wd = 0
#         Hd = 0
#         if H < W:
#             Wd = idx.item() + 1
#         elif H > W:
#             Hd = idx.item() + 1
#
#         vecs = []
#         for element in L:
#             wl = math.floor(2 * w / (element + 1))
#             wl2 = math.floor(wl / 2 - 1)
#
#             if element + Wd == 1:
#                 b = 0
#             else:
#                 b = (W - wl) / (element + Wd - 1)
#             cenW = (
#                 torch.floor(wl2 + torch.tensor(range(element - 1 + Wd + 1)) * b) - wl2
#             )  # center coordinates
#             if element + Hd == 1:
#                 b = 0
#             else:
#                 b = (H - wl) / (element + Hd - 1)
#             cenH = (
#                 torch.floor(wl2 + torch.tensor(range(element - 1 + Hd + 1)) * b) - wl2
#             )  # center coordinates
#
#             # for i in cenH.tolist():
#             #     for j in cenW.tolist():
#             #         if wl == 0:
#             #             continue
#             #         R = x[:, :, (int(i_) + torch.Tensor(range(wl)).long()).tolist(), :]
#             #         R = R[:, :, :, (int(j_) + torch.Tensor(range(wl)).long()).tolist()]
#             #         vecs.append(F.max_pool2d(R, (R.size(-2), R.size(-1))))
#         return torch.cat(vecs, dim=2)


class PCA(nn.Module):
    def __init__(self, n_components=None):
        super().__init__()
        pretrained_url = "http://ndd.iti.gr/visil/pca_resnet50_vcdb_1M.pth"
        white = torch.hub.load_state_dict_from_url(pretrained_url)
        idx = torch.argsort(white["d"], descending=True)[:n_components]
        # d = white["d"][idx]
        # V = white["V"][:, idx]
        # D = torch.diag(1.0 / torch.sqrt(d + 1e-7))
        white_d = white["d"][idx]
        white_v = white["V"][:, idx]
        one_over_white_d_square_root = torch.diag(1.0 / torch.sqrt(white_d + 1e-7))
        self.mean = nn.Parameter(white["mean"], requires_grad=False)
        # self.DVt = nn.Parameter(torch.mm(D, V.T).T, requires_grad=False)
        self.dv_transpose = nn.Parameter(
            torch.mm(one_over_white_d_square_root, white_v.T).T, requires_grad=False
        )

    def forward(self, logits):
        logits -= self.mean.expand_as(logits)
        logits = torch.matmul(logits, self.dv_transpose)
        logits = F.normalize(logits, p=2, dim=-1)
        return logits


class L2Constrain:
    def __init__(self, axis=-1, eps=1e-6):
        self.axis = axis
        self.eps = eps

    def __call__(self, module):
        if hasattr(module, "weight"):
            module_weight_data = module.weight.image
            module.weight.image = F.normalize(
                module_weight_data, p=2, dim=self.axis, eps=self.eps
            )


class Attention(nn.Module):
    def __init__(self, dims, norm=False):
        super().__init__()
        self.norm = norm
        if self.norm:
            self.constrain = L2Constrain()
        else:
            self.transform = nn.Linear(dims, dims)
        self.context_vector = nn.Linear(dims, 1, bias=False)
        self.reset_parameters()

    def forward(self, input_x):
        if self.norm:
            weights = self.context_vector(input_x)
            weights = torch.add(torch.div(weights, 2.0), 0.5)
        else:
            x_tr = torch.tanh(self.transform(input_x))
            weights = self.context_vector(x_tr)
            weights = torch.sigmoid(weights)
        input_x = input_x * weights
        return input_x, weights

    def reset_parameters(self):
        if self.norm:
            nn.init.normal_(self.context_vector.weight)
            self.constrain(self.context_vector)
        else:
            nn.init.xavier_uniform_(self.context_vector.weight)
            nn.init.xavier_uniform_(self.transform.weight)
            nn.init.zeros_(self.transform.bias)

    def apply_contraint(self):
        if self.norm:
            self.constrain(self.context_vector)
