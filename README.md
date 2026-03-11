# Sandboxed LLM Agent

An agentic coding assistant that gives an LLM its own isolated workspace to write and run Python code. The LLM gets a complete environment — it can create files, build projects, run scripts — but everything stays contained inside a hardened Docker sandbox. Nothing leaks to the host beyond a single mounted directory.

## The Idea

The LLM doesn't run code on your machine. Instead, it gets its own **sandboxed environment**:

```
┌─── Your machine ──────────────────────────────────────────────┐
│                                                               │
│   main.py → Agent → LLM (llama.cpp)                          │
│                │                                              │
│                │  "run this code"                              │
│                ▼                                              │
│   ┌─── Docker sandbox ──────────────────────────────┐        │
│   │                                                  │        │
│   │   /workspace/          ← LLM's world             │        │
│   │     ├── script.py      ← LLM creates files here  │        │
│   │     ├── data.json      ← LLM reads/writes freely │        │
│   │     └── output/        ← results persist here     │        │
│   │                                                  │        │
│   │   /tmp/                ← temp scripts (RAM only)  │        │
│   │                                                  │        │
│   │   No network · No root · No system access         │        │
│   └──────────────────────────────────────────────────┘        │
│                │                                              │
│                │  bind mount                                  │
│                ▼                                              │
│   ~/git_ws/_sandbox/       ← only this host dir is shared     │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

The `/workspace` directory inside the container is bind-mounted to a real directory on the host (`SANDBOX_WORKDIR` in `.env`). Files the LLM creates there persist and are visible on the host. Everything else — the system, network, other files — is locked down.

The agent has three tools: `python` (execute code in the sandbox), `load_skill` (load task-specific instructions), and `read_resource` (load extra docs referenced by skills).

## Sandboxing: How It Works

### Long-running container + exec pattern

Instead of spinning up a new container per code execution (slow, ~1s overhead each), the sandbox uses a **persistent container**:

1. **First call** — `docker compose up -d` starts the container once. It runs `sleep infinity` to stay alive.
2. **Each execution** — `docker compose exec` runs `python3` inside the already-running container. This is fast (~50ms overhead).
3. **Shutdown** — `docker compose down` on process exit (registered via `atexit`).

### Execution flow

Each `execute(code)` call:

1. Writes the code to a temp file in the container's `/tmp` (tmpfs, exists only in RAM) via `docker compose exec sh -c "cat > /tmp/_run_<id>.py"` with stdin piping
2. Runs `docker compose exec python3 /tmp/_run_<id>.py`
3. Captures stdout/stderr and returns it to the agent
4. Deletes the temp script

### Security hardening (docker-compose.yml)

All security configuration lives in `docker-compose.yml` — the single source of truth:

| Setting | Value | Purpose |
|---|---|---|
| `network_mode` | `none` | No network access — prevents data exfiltration, C2, or downloading malicious packages |
| `cap_drop` | `ALL` | Drops all Linux capabilities (no mount, no raw sockets, no ptrace, etc.) |
| `security_opt` | `no-new-privileges` | Prevents privilege escalation via setuid/setgid binaries |
| `read_only` | `true` | Root filesystem is read-only — LLM can't modify system files or install packages at runtime |
| `tmpfs` | `/tmp:size=64M` | In-memory filesystem for temp scripts — gone when container stops, capped at 64MB |
| `memory` | `512M` | Hard memory limit — prevents OOM attacks on the host |
| `cpus` | `0.5` | 50% of one CPU core — prevents CPU starvation |
| `pids_limit` | `64` | Max 64 processes — prevents fork bombs |

### Non-root user (Dockerfile.sandbox)

The container image creates a dedicated `sandbox` user. All code runs as this unprivileged user, not root. Even if the LLM finds an exploit, the attack surface is minimal.

### Volume mounts

The host's working directory is mounted at `/workspace` inside the container. Additional mounts can be added in `docker-compose.yml`:

```yaml
volumes:
  - ${SANDBOX_WORKDIR:-.}:/workspace       # default, controlled via env var
  - /host/datasets:/data:ro                # read-only data access
  - /host/output:/output:rw                # writable output directory
```

The `SANDBOX_WORKDIR` env var is set automatically by `tool_python.py` based on the `--workdir` CLI argument.

## Setup

### Prerequisites

- Python 3.11+
- Docker with `docker compose` (v2)
- A running llama.cpp server with a tool-calling model

### Workspace directory

The sandbox mounts a host directory at `/workspace` inside the container. By default this is `/tmp/sandbox_workspace`, but you can override it via `SANDBOX_WORKDIR` in your `.env` file or as an environment variable.

**You must create this directory before starting the agent.** Docker will auto-create it if it doesn't exist, but it will be owned by `root`, which means the unprivileged `sandbox` user inside the container won't be able to write to it.

```bash
# Create the default workspace directory
mkdir -p /tmp/sandbox_workspace

# Or, if using a custom path (must match SANDBOX_WORKDIR in .env):
mkdir -p /path/to/your/workspace
```

> **Important:** Do not point `SANDBOX_WORKDIR` at the project's own source directory. The sandbox executes LLM-generated code and must not have write access to the agent's source files.

### Install & run

```bash
# Ensure your user can access Docker
sudo usermod -aG docker $USER  # then re-login

# Install Python dependencies
pip install -r requirements.txt

# Create the sandbox workspace directory
mkdir -p /tmp/sandbox_workspace

# Start the agent (first run builds the sandbox image automatically)
python main.py --server http://localhost:8080 --workdir /path/to/project
```

### Customizing the sandbox

**Change resource limits** — edit `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 1G    # more memory
      cpus: "1.0"   # full core
```

**Add Python packages** — edit `Dockerfile.sandbox`:
```dockerfile
RUN pip install --no-cache-dir numpy pandas matplotlib scikit-learn
```
Then rebuild: `docker compose -f docker-compose.yml build`

**Mount additional directories** — edit `docker-compose.yml`:
```yaml
volumes:
  - ${SANDBOX_WORKDIR:-.}:/workspace
  - /home/user/datasets:/data:ro
```

## Docker Basics

### Core concepts

- **Image** — A read-only template. Built from a Dockerfile. Contains the OS, packages, and config.
  - **Dockerfile** — Recipe to build an image. Each instruction (`FROM`, `RUN`, `COPY`) creates a cached layer.
- **Container** — A running instance of an image. Has its own filesystem, network, and process space. Isolated from the host.
  - **Volume/Mount** — Connects a host directory to a path inside the container. Changes are visible on both sides.
- **Service** — A named entry in `docker-compose.yml` (e.g. `sandbox`). Describes which image to use and how to run the container (volumes, limits, etc.). `docker compose up` turns services into running containers.
  - **docker-compose.yml** — Declarative config for one or more services. Defines how they run (ports, volumes, limits, networks).

### How Docker isolation works

A container is **not** a VM. It uses Linux kernel features to isolate processes:

- **Namespaces** — each container gets its own view of PIDs, network, mounts, users
- **Cgroups** — enforce resource limits (memory, CPU, PIDs)
- **Capabilities** — fine-grained root permissions that can be individually dropped
- **Seccomp** — syscall filtering (blocks dangerous kernel calls)

The container shares the host kernel but can't see or affect other processes, files, or network interfaces outside its namespace.

### Essential commands

```bash
# Images
docker build -t myimage .              # Build image from Dockerfile in current dir
docker images                          # List all images
docker rmi myimage                     # Remove an image

# Containers
docker run -d --name mybox myimage     # Start container in background
docker ps                              # List running containers
docker ps -a                           # List all containers (including stopped)
docker stop mybox                      # Stop a container
docker rm mybox                        # Remove a stopped container
docker logs mybox                      # View container stdout/stderr
docker exec -it mybox bash             # Open interactive shell inside container

# Compose (multi-container / declarative)
docker compose up -d                   # Start services defined in docker-compose.yml
docker compose down                    # Stop and remove containers
docker compose ps                      # List running compose services
docker compose exec sandbox bash       # Shell into a specific service
docker compose build                   # Rebuild images
docker compose logs -f                 # Tail logs from all services

# Cleanup
docker system prune                    # Remove unused containers, networks, images
docker volume prune                    # Remove unused volumes
```

### Dockerfile vs docker-compose.yml

| | Dockerfile | docker-compose.yml |
|---|---|---|
| **Purpose** | *What's inside* the image | *How to run* the container |
| **Defines** | Base image, packages, files, user | Network, volumes, limits, security |
| **When used** | `docker build` (build time) | `docker compose up` (run time) |
| **Analogy** | Blueprint for building a house | Rules for living in it |

## Project structure

```
├── main.py                 # CLI entry point
├── agent.py                # Agentic loop with tool handling
├── tool_python.py          # Sandboxed Python interpreter (compose exec)
├── docker-compose.yml      # Container config (security, limits, volumes)
├── Dockerfile.sandbox      # Sandbox image definition
├── skills/                 # Skill definitions (progressive disclosure)
│   ├── read-file/
│   ├── write-file/
│   ├── list-directory/
│   ├── search-files/
│   └── run-command/
└── requirements.txt
```
