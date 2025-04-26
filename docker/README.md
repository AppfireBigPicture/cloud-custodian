## Cloud Custodian Docker Setup

### Overview
Provides Docker configuration, dependencies, and scripts for running Cloud Custodian (c7n) in a container.

### Directory Layout

```
.
├── config/                  # Cloud Custodian configuration files
├── scripts/                 # Automation scripts for c7n-org, c7n-mailer, policy generation
├── Dockerfile               # Base image, non-sensitive ENV vars
└── Dockerfile-local         # For Netskope-enabled hosts; uses netskope-cert-bundle.pem
```

### Dockerfiles

#### `Dockerfile`

- **FROM**: Base image
- **ENV**: Non-sensitive variables (hard-coded)
- **COPY**: `config/`, `scripts/`, `entrypoint.sh`
- **ENTRYPOINT**: `["/entrypoint.sh"]`
- **CMD**: `["c7n-pipeline.sh"]`

#### `Dockerfile-local`
- Extends `Dockerfile`
- **ADD**: `netskope-cert-bundle.pem`
- Configures certificate bundle for Netskope environments

### Environment Variables

| Type               | Definition                          | Retrieval                         |
|--------------------|-------------------------------------|-----------------------------------|
| **Non-sensitive**  | Declared via `ENV` in Dockerfiles   | Available at build time           |
| **Sensitive**      | Slack webhook, AWS keys, etc.       | Fetched from AWS SSM by entrypoint |

### Scripts

#### `entrypoint.sh`
- Retrieves sensitive variables from SSM
- Exports them into shell environment

#### `scripts/policy_generator.py`
- Generates c7n policy files
- Consumes ENV vars set by `entrypoint.sh`

#### `scripts/{c7n-org, c7n-mailer}-launcher.sh`
- Launches c7n-org or c7n-mailer pipelines

### GitHub Actions Workflow

```yaml
name: Docker CI

on: [push]

jobs:
  validate:
    uses: hadolint/hadolint-action@v2

  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t c7n-image .
      # future: push to registry
```

- **Hadolint**: Lints Dockerfiles
- **Docker Build**: Builds image

### Container Invocation

- **Default**: runs `entrypoint.sh` → `c7n-pipeline.sh`
- **Override CMD**:
  ```bash
  docker run c7n-image /path/to/custom-script.sh
  ```  
