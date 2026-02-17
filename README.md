# Neuronest

**Production-ready AI systems, deployed into your own cloud.**

Neuronest is a monorepo of Python ML/CV microservices deployed on Google Cloud Platform. Each service ships with its full stack — cloud infrastructure, serving layer, async job processing, cost-optimized auto-scaling, and source code — ready to run in any GCP project.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Client Request                             │
└──────────┬──────────────────────┬───────────────────────┬───────────┘
           │ sync                 │ async                  │ real-time
           ▼                     ▼                        ▼
    ┌─────────────┐     ┌──────────────┐        ┌──────────────────┐
    │  Cloud Run  │     │  Cloud Run   │        │   Vertex AI      │
    │  (FastAPI)  │     │    Jobs      │        │   Endpoint       │
    └──────┬──────┘     └──────┬───────┘        └────────┬─────────┘
           │                   │                         │
           ▼                   ▼                         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                     Shared Core Library                         │
    │  GCP Clients · Path Abstraction · Schemas · Serialization      │
    └──────┬──────────────┬───────────────────┬───────────┬──────────┘
           │              │                   │           │
           ▼              ▼                   ▼           ▼
      ┌─────────┐  ┌────────────┐    ┌──────────┐  ┌──────────────┐
      │   GCS   │  │ Firestore  │    │ Vertex AI│  │   Cloud      │
      │ Buckets │  │  (Jobs DB) │    │ (Models) │  │  Scheduler   │
      └─────────┘  └────────────┘    └──────────┘  └──────────────┘
```

Each service supports **three prediction modes**:

| Mode | Flow | Use case |
|------|------|----------|
| **Async** | Request → Cloud Run Job → poll Firestore → fetch results from GCS | Large-scale batch processing |
| **Sync** | Request → blocking call with polling → response | Simple integrations |
| **Real-time** | Request → Vertex AI endpoint → instant response | Low-latency inference |

---

## Services

### Object Detection

YOLO-based image analysis returning bounding boxes, class labels, and confidence scores.

```
POST /object_detection/api/v1/object_detection/detect_objects           # async
POST /object_detection/api/v1/object_detection/detect_objects_real_time  # real-time
```

- Model: Ultralytics YOLOv5x6 (configurable)
- Input: images (GCS paths or base64-encoded)
- Output: bounding boxes with `x_min, y_min, x_max, y_max, score, class_id, class_name`

### People Counting

Counts people crossing a virtual line in video using YOLO detection + dlib correlation tracking + centroid-based identity management.

```
POST /people_counting/api/v1/people_counter/count_people                # async
POST /people_counting/api/v1/people_counter/count_people_real_time      # real-time
```

- Input: video (GCS path or inline)
- Output: timestamped entry/exit events with direction (`UP` / `DOWN`)

### Video Comparator

Computes similarity scores between video pairs using deep feature embeddings (torchvision), with GCS-backed embedding caching.

```
POST /video_comparator/api/v1/video_comparator/compare_videos           # async
POST /video_comparator/api/v1/video_comparator/compare_videos_real_time  # real-time
```

- Input: two video paths
- Output: `similarity_score: float`

### Model Instantiator

Manages model lifecycle — deploys models to Vertex AI on demand and undeploys idle ones to optimize costs.

```
POST /model_instantiator/api/v1/instantiator/instantiate
POST /model_instantiator/api/v1/uninstantiator/uninstantiate
POST /model_instantiator/api/v1/uninstantiator/uninstantiate_logs_conditioned
```

---

## Project Structure

```
neuronest/
├── shared/                  # Core library (core package)
│   ├── core/
│   │   ├── client/          # API client abstractions (async jobs, real-time)
│   │   ├── google/          # GCP wrappers (Storage, Firestore, Vertex AI, Cloud Run)
│   │   ├── routes/          # API endpoint path definitions
│   │   ├── schemas/         # Pydantic models for all modules
│   │   ├── services/        # Asset reading, resizing, deployment status
│   │   ├── serialization/   # Image, DataFrame, array, bytes serializers
│   │   ├── packages/        # Abstract base classes (OnlinePredictionModel)
│   │   └── path.py          # Universal path: gs:// | https:// | local
│   ├── iac/                 # Terraform modules (abstract + base infra)
│   └── tests/
├── object-detection/        # YOLO object detection service
│   ├── object_detection/
│   │   ├── app/             # FastAPI routes & dependencies
│   │   ├── jobs/            # Async job workers
│   │   └── modules/         # YOLO model wrapper
│   ├── conf/config.yaml
│   └── tests/
├── people-counting/         # Video people counting service
│   ├── people_counting/
│   │   ├── app/
│   │   ├── jobs/
│   │   ├── centroid_tracker.py
│   │   └── people_counter.py
│   ├── conf/config.yaml
│   └── tests/
├── video-comparator/        # Video similarity service
│   ├── video_comparator/
│   │   ├── app/
│   │   ├── jobs/
│   │   ├── modules/         # Feature extraction
│   │   └── services/        # Embedding caching
│   ├── conf/config.yaml
│   └── tests/
├── model-instantiator/      # Model lifecycle manager
│   ├── model_instantiator/
│   │   └── app/
│   ├── conf/config.yaml
│   └── tests/
├── .github/                 # CI/CD workflows & reusable actions
├── Dockerfile               # Multi-stage build (all services)
└── .pre-commit-config.yaml  # black, flake8, isort, pylint, toml-sort, terraform fmt
```

Every service follows the same structure: `app/` (FastAPI routes), `jobs/` (async workers), `modules/` (ML models), and `conf/config.yaml` (OmegaConf configuration with env var substitution).

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Language** | Python 3.11 |
| **ML/CV** | PyTorch, torchvision, Ultralytics (YOLO), dlib, OpenCV |
| **API** | FastAPI, Gunicorn, Uvicorn |
| **Cloud** | GCP — Cloud Run, GCS, Firestore, Vertex AI, Cloud Scheduler |
| **IaC** | Terraform |
| **CI/CD** | GitHub Actions on self-hosted Kubernetes runners |
| **Packaging** | Poetry, Docker |
| **Schemas** | Pydantic, OmegaConf |
| **Quality** | black, flake8, isort, pylint, pytest |

---

## Getting Started

### Prerequisites

- Python 3.11 (`>3.11,<3.12`)
- [Poetry](https://python-poetry.org/)
- GCP credentials (for integration tests and deployment)

### Installation

Each module has its own Poetry project. Install from the module directory:

```bash
cd shared/
./install.sh                        # uses python3.11 by default
./install.sh -p /path/to/python     # specify python path
```

Repeat for any service module (`object-detection/`, `people-counting/`, etc.).

Services depend on the shared `core` library via a local path dependency (`develop = true`), so changes to `shared/` are immediately reflected.

### Running a Service Locally

```bash
cd object-detection/
poetry run gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8080 \
    object_detection.app.main:app
```

### Docker

```bash
docker build \
    --build-arg REPOSITORY_NAME=object-detection \
    --build-arg PACKAGE_NAME=object_detection \
    -t neuronest-object-detection .
```

---

## Testing

```bash
# Unit tests (no GCP credentials required)
pytest -x -n auto shared/tests/unit_tests -vv
pytest -x -n auto object-detection/tests/unit_tests -vv

# Single test file
pytest object-detection/tests/unit_tests/test_file.py -vv

# Single test
pytest object-detection/tests/unit_tests/test_file.py::test_name -vv

# Integration tests (requires GCP credentials + running services)
pytest -x -n auto object-detection/tests/integration_tests -vv
```

---

## Linting & Formatting

Pre-commit hooks enforce code quality. Install once, they run on every commit:

```bash
pre-commit install
pre-commit run --all-files          # run manually
```

**Hooks:** black (formatting, line length 88) · flake8 · isort (black profile) · pylint · toml-sort · terraform fmt

---

## Commit Convention

Enforced by pre-commit hook. Format:

```
(<type>) [optional scope] Message starting with uppercase
```

**Types:** `feat` · `fix` · `hotfix` · `update` · `refactor` · `clean` · `test` · `config` · `ci` · `doc` · `wip` · `merge`

**Examples:**

```
(feat) Add new detection endpoint
(fix) [object-detection] Correct bounding box calculation
(refactor) Extract embedding cache into dedicated service
```

---

## CI/CD

The CI/CD pipeline runs on GitHub Actions with self-hosted Kubernetes runners. A reusable workflow (`abstract_online_prediction_model.yaml`) orchestrates the full lifecycle for each service:

1. **Terraform** — Provision GCP infrastructure (Cloud Run, GCS, Firestore, IAM)
2. **Docker Build** — Build training and serving images, push to Artifact Registry
3. **Train** — Run model training on Vertex AI
4. **Deploy** — Register model, deploy to Cloud Run and Vertex AI endpoints
5. **Integration Tests** — Run end-to-end tests against live services

---

## Authors

**Guillaume Ligner** and **Côme Arvis** — ML engineers who productized years of deployment patterns into a reusable platform.

---

*Neuronest — Stop choosing between speed and ownership. Get both.*
