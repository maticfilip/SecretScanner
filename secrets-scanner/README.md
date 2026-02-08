# Secrets Scanner (A challenge for students)

A toy secrets scanner for Git repositories and local directories.
THIS IS NOT FOR PROD USE :)

## Architecture

- **Scanner Service** (port 8001): REST API that scans file content for secrets using regex patterns and entropy detection
- **Orchestrator Service** (port 8000): Clones GitHub repos or scans local directories, orchestrates parallel scanning using multiprocessing

## Requirements

- Docker
- Docker Compose

## Usage

### Start the services

```bash
docker-compose up --build
```

### Scan a GitHub repository

```bash
curl -X POST http://localhost:8000/scan-repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo.git"}'
```

### Scan a local directory

The orchestrator mounts `./test-repos` to `/repos` inside the container. Place your repository in the `test-repos` directory:

```bash
# Copy your repository
cp -r /path/to/your/repo test-repos/my-repo

# Scan it
curl -X POST http://localhost:8000/scan-local \
  -H "Content-Type: application/json" \
  -d '{"path": "/repos/my-repo"}'
```

The scanner will scan all files (excluding hidden files like `.git`) and check for secrets.

## Detectors

The scanner uses two detection methods: 1) Regex-based detectors, and 2) Entropy-based detector.

## Health Checks

```bash
# Check orchestrator health
curl http://localhost:8000/health

# Check scanner health
curl http://localhost:8001/health
```

## Direct Scanner API

You can also use the scanner service directly:

```bash
curl -X POST http://localhost:8001/scan \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.py",
    "content": "aws_access_key = \"AKIAIOSFODNN7EXAMPLE\""
  }'
```

## Your Tasks:

### 1. Build a Web UI

Create a nice web interface :)

Example
* Form inputs: repo address
* Submit button to trigger scan
* Display results with color coding (red for secrets found)
* A loading spinner

### 2. LLM-Powered Security Report

Add intelligent analysis:


* Based on scan results, use an LLM to generate a mitigation report with actionable recommendations
* Use a free LLM API (Gemini, Mistral, etc.)


### 3. Private repositories

 * Add support for private GitHub repositories.



**You are welcome to enrich the codebase (including the test-repos directory)  with your own ideas**
**You can redistribute your derived work how you prefer**

## Resources Provided:

* This repository.

## What you have to provide:

* You are free to add new services in the language that you prefer.
* The full project must be runnable with `docker-compose up --build`.
* A short description of what you did + instructions on how to test it: fill INSTRUCTIONS.md 

* Create a file <your name>.zip with your solution. It could be as easy as
  ```bash
  git archive --format=zip --output=<your name>.zip HEAD
  ```
* Share your archive with us!

!! **Important** we expect to `unzip` the file, `cd` into the directory, run `docker compose up --build` to run it.
