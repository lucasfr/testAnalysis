# 📘 circadiaBase_Docker — Tutorial

This guide walks you through setting up, running, and using the circadiaBase_Docker environment for chronobiology and actigraphy research.

---

## 📋 Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [GitHub Actions — Auto-configuration](#3-github-actions--auto-configuration)
4. [Configuration](#4-configuration)
5. [Building and Running](#5-building-and-running)
6. [Using JupyterLab](#6-using-jupyterlab)
7. [Using condor_pipeline](#7-using-condor_pipeline)
8. [Using RStudio Server](#8-using-rstudio-server)
9. [Working with Shared Files](#9-working-with-shared-files)
10. [Managing the Stack](#10-managing-the-stack)
11. [Switching R Profiles](#11-switching-r-profiles)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (Mac/Windows) or **Docker Engine + Compose plugin** (Linux)
  - Download: https://www.docker.com/products/docker-desktop/
  - Minimum recommended: 8 GB RAM allocated to Docker, 20 GB disk space
- **Git**
  - Download: https://git-scm.com/

To verify your installation:

```bash
docker --version        # Should print Docker version 24.x or later
docker compose version  # Should print Docker Compose version 2.x or later
git --version           # Should print git version 2.x or later
```

> **Apple Silicon (M1/M2/M3/M4):** Both services are fully supported natively. The RStudio service uses `jmgirard/rstudio2u` which has ARM64 support built in.

---

## 2. Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/circadia-bio/circadiaBase_Docker.git
cd circadiaBase_Docker
```

---

## 3. GitHub Actions — Auto-configuration

This repo ships with a GitHub Actions workflow at `.github/workflows/setup-env.yml` that runs automatically on every push to `main`.

### What it does

**Generates `.env` from the repo name**

The workflow reads the repository name, converts it to a Docker-safe string (lowercase, special characters replaced with underscores), and writes it as `IMAGE_NAME` in `.env`. It preserves all other variables in the file (`DISABLE_AUTH`, `RSTUDIO_PROFILE`, etc.).

For example:

| Repo name | Generated `IMAGE_NAME` |
|---|---|
| `circadiaBase_Docker` | `circadiabase_docker` |
| `Per3_Study` | `per3_study` |
| `my-actigraphy-project` | `my-actigraphy-project` |

**Resets the README to a stub (first push only)**

If the README still contains the original placeholder text (e.g. `_Brief description_`), the workflow replaces it with a minimal stub pre-filled with the repo name and Circadia Lab authorship. On all subsequent pushes the README is left untouched.

### Enabling write permissions

The workflow needs permission to commit back to the repo. Enable this once per repo:

1. Go to your repo on GitHub
2. **Settings → Actions → General**
3. Under **Workflow permissions**, select **Read and write permissions**
4. Click **Save**

### What happens on first push

```
You push to main
       │
       ▼
Workflow runs
       │
       ├── .env exists?  ──Yes──▶ Update IMAGE_NAME in place
       │                  No────▶ Copy .env.example → .env, set IMAGE_NAME
       │
       ├── Commit & push .env
       │
       └── README has placeholders?  ──Yes──▶ Reset to stub, commit & push
                                       No────▶ Skip (README already customised)
```

### Working locally without GitHub Actions

If you are not pushing to GitHub (e.g. running locally on a cloned copy), create `.env` manually:

```bash
cp .env.example .env
```

The default `IMAGE_NAME=circadia_base` will work fine for local use. Edit it if you want the image named after your project.

---

## 4. Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` and review the settings:

```bash
# Docker image name — set automatically from repo name by GitHub Actions
IMAGE_NAME=circadia_base

# Disable RStudio password (suitable for local development only)
DISABLE_AUTH=true

# Services to run
# Options: both (default) | jupyter | rstudio
COMPOSE_PROFILES=both

# Install condor_pipeline in editable mode
# Set to true if the repo includes a pyproject.toml at the root
INSTALL_PACKAGE=true

# RStudio build profile
# Options: minimal (default) | no-stan | full
RSTUDIO_PROFILE=minimal
```

### Choosing which services to run

The `COMPOSE_PROFILES` variable controls which containers are started:

| Value | Services started | Use case |
|---|---|---|
| `both` (default) | JupyterLab + RStudio | Full environment |
| `jupyter` | JupyterLab only | Python-only analyses |
| `rstudio` | RStudio only | R-only analyses |

### Choosing an RStudio profile

The `RSTUDIO_PROFILE` variable controls which R packages are included:

| Profile | Stan/brms | lunaR | Approx. build time | Recommended for |
|---|---|---|---|---|
| `minimal` | ❌ | ❌ | ~5–8 min | Getting started, most analyses |
| `no-stan` | ❌ | ✅ | ~10–15 min | Actigraphy with lunaR |
| `full` | ✅ | ✅ | ~30–40 min | Bayesian modelling |

For most use cases, start with `minimal`. You can always rebuild with a heavier profile later.

---

## 5. Building and Running

### First run (builds Docker images)

```bash
docker-compose up --build
```

This will:
1. Build the Python/JupyterLab image from `jupyter/Dockerfile`
2. Build the R/RStudio image from `rstudio/Dockerfile.${RSTUDIO_PROFILE}`
3. Start both services

> The first build takes several minutes depending on your internet connection and chosen profile. Subsequent runs use Docker's layer cache and start in seconds.

### Subsequent runs

```bash
docker-compose up
```

### Running a single service

```bash
docker-compose up jupyter   # JupyterLab only
docker-compose up rstudio   # RStudio only
```

### Running in the background (detached mode)

```bash
docker-compose up -d
```

To stop detached services:

```bash
docker-compose down
```

---

## 6. Using JupyterLab

Once running, open your browser and navigate to:

```
http://localhost:8889/lab
```

No token or password is required.

### Available Python packages

The JupyterLab environment includes a full scientific stack for chronobiology research:

```python
import pyActigraphy      # Actigraphy analysis
import mne               # EEG/MEG processing
import yasa              # Sleep staging
import EntropyHub as eh  # Entropy methods
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from sklearn import ...
from scipy import ...
```

### Creating a new notebook

1. Click the **+** button in the left sidebar
2. Select **Python 3 (ipykernel)** under Notebook
3. Start coding

### Saving your work

All files saved inside `/home/jovyan/<IMAGE_NAME>/` are written to the shared project volume and will persist after the container stops. This maps directly to the root of your cloned repository on your host machine.

---

## 7. Using condor_pipeline

`condor_pipeline` is the Circadia Lab's core actigraphy sleep analysis library. It is included in the repository and installed automatically in editable mode when `INSTALL_PACKAGE=true` is set in `.env`.

### Enabling the editable install

Ensure your `.env` contains:

```bash
INSTALL_PACKAGE=true
```

Then rebuild the Jupyter image:

```bash
docker-compose build --no-cache jupyter
```

### Importing in a notebook

```python
from condor_pipeline.pipeline import SleepPipeline
from condor_pipeline.viz.actogram import plot_actogram
```

### Single file analysis

```python
from condor_pipeline.pipeline import SleepPipeline

pipe = SleepPipeline(
    "data/raw/subject_01.txt",
    device="acttrust",       # or "actiwatch"
    gap_threshold=120.0,    # seconds — flags timestamp gaps
    wake_thresh=60,         # minutes — WASO threshold
    export_offwrist=True,   # writes off-wrist CSV alongside input
)

result = pipe.run()

# Per-night sleep statistics
print(result.nights)

# Plot actogram
result.plot()
```

### Batch processing

```python
results = SleepPipeline.batch(
    "data/raw/",
    device="acttrust",
    pattern="*.txt",
)

for r in results:
    print(r.subject_id, r.nights)
    r.plot()
```

### PipelineResult attributes

| Attribute | Type | Description |
|---|---|---|
| `subject_id` | str | Derived from input filename stem |
| `source_file` | Path | Path to the raw input file |
| `df` | DataFrame | Final working DataFrame with all state columns |
| `nights` | DataFrame | Per-night sleep statistics |
| `issues` | DataFrame | Timestamp consistency issues (empty if none) |
| `offwrist_csv` | Path or None | Path to exported off-wrist CSV |

### Supported devices

| Device string | Format |
|---|---|
| `acttrust` | Condor Instruments ActTrust |
| `actiwatch` | Philips Actiwatch |

---

## 8. Using RStudio Server

Once running, open your browser and navigate to:

```
http://localhost:8787
```

No password is required (`DISABLE_AUTH=true`).

### Available R packages

The RStudio environment includes packages for sleep and circadian research:

```r
# Data wrangling & visualisation (tidyverse pre-installed)
library(tidyverse)
library(ggpubr)
library(patchwork)
library(ggridges)

# Statistical modelling
library(lme4)
library(lmerTest)
library(emmeans)
library(effectsize)

# Circadian & sleep analysis
library(GGIR)
library(ActCR)
library(circacompare)
library(cosinor)
library(cosinor2)

# Bayesian (no-stan and full profiles only)
library(bayesplot)
library(tidybayes)

# brms and rstanarm (full profile only)
library(brms)
library(rstanarm)
```

### Setting your working directory

Your project files are mounted at `/home/rstudio/<IMAGE_NAME>/`. Set this as your working directory in RStudio:

```r
setwd("/home/rstudio/circadia_base")
```

Or use the **Files** pane → navigate to the folder → **More** → **Set As Working Directory**.

---

## 9. Working with Shared Files

Both services mount the same project directory, so files created in one are immediately visible in the other.

```
Host machine:           ~/circadiaBase_Docker/
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
  JupyterLab container              RStudio container
  /home/jovyan/circadia_base/   /home/rstudio/circadia_base/
```

For example:
- Save a cleaned `.csv` from a Python notebook → open and model it directly in RStudio
- Export R model outputs → load them in Python for further analysis or visualisation

### Recommended project layout

```
circadiaBase_Docker/
├── data/
│   ├── raw/          # Raw actigraphy, EEG, or other input files
│   └── processed/    # Cleaned/processed outputs
├── notebooks/        # JupyterLab notebooks (.ipynb)
├── scripts/          # R scripts (.R) or Python scripts (.py)
├── figures/          # Generated plots and figures
└── results/          # Model outputs, summary tables
```

---

## 10. Managing the Stack

### Stop all services

```bash
docker-compose down
```

### Stop and remove all containers, networks, and volumes

```bash
docker-compose down -v
```

### View running containers

```bash
docker ps
```

### View logs

```bash
docker-compose logs jupyter    # JupyterLab logs
docker-compose logs rstudio    # RStudio logs
docker-compose logs -f         # Follow all logs in real time
```

### Rebuild a single service after Dockerfile changes

```bash
docker-compose build --no-cache jupyter
docker-compose build --no-cache rstudio
```

---

## 11. Switching R Profiles

To switch from `minimal` to a heavier profile, edit `.env`:

```bash
RSTUDIO_PROFILE=no-stan   # or full
```

Then rebuild the RStudio service:

```bash
docker-compose build --no-cache rstudio
docker-compose up
```

> Note: switching profiles rebuilds the R image from scratch. The JupyterLab image is unaffected.

---

## 12. Troubleshooting

### Cannot connect to JupyterLab or RStudio

Check that the containers are running:

```bash
docker ps
```

Both `circadia_base:latest` and `circadia_base_r:latest` should appear with status `Up`. If not, check the logs:

```bash
docker-compose logs
```

Make sure you're using the correct URLs:
- JupyterLab: `http://localhost:8889/lab` (note: `/lab` suffix required)
- RStudio: `http://localhost:8787`

### Build fails with a package error

If a specific package fails to install, try rebuilding with no cache:

```bash
docker-compose build --no-cache rstudio
```

If the error persists, check the package name and version in the relevant Dockerfile under `rstudio/`.

### `IMAGE_NAME` not set / image not found

Ensure your `.env` file exists and contains `IMAGE_NAME`:

```bash
cat .env
```

If missing, recreate it:

```bash
cp .env.example .env
```

### Port already in use

If ports 8889 or 8787 are already in use on your machine, edit `docker-compose.yml` to use different host ports:

```yaml
ports:
  - "8890:8888"   # Change 8889 to any free port
```

### Apple Silicon — RStudio not loading

Ensure Docker Desktop has **"Use Rosetta for x86/amd64 emulation"** disabled — the RStudio service (`jmgirard/rstudio2u`) runs natively on ARM64 and does not require Rosetta.

### Files not persisting after container restart

Ensure you are saving files inside the mounted volume directory:
- JupyterLab: `/home/jovyan/<IMAGE_NAME>/`
- RStudio: `/home/rstudio/<IMAGE_NAME>/`

Files saved outside these directories (e.g. in `/tmp`) will be lost when the container stops.

---

## Further Reading

- [pyActigraphy documentation](https://pyactigraphy.readthedocs.io/)
- [MNE-Python documentation](https://mne.tools/stable/index.html)
- [YASA documentation](https://raphaelvallat.com/yasa/build/html/index.html)
- [GGIR documentation](https://cran.r-project.org/web/packages/GGIR/vignettes/GGIR.html)
- [circacompare on CRAN](https://cran.r-project.org/web/packages/circacompare/index.html)
- [Rocker Project](https://rocker-project.org/)
- [r2u — CRAN as Ubuntu Binaries](https://github.com/eddelbuettel/r2u)

---

*Tutorial maintained by the [Circadia Lab](https://github.com/circadia-bio). For issues or suggestions, open a ticket on GitHub.*
