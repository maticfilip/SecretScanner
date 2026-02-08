import os
import tempfile
import shutil
from multiprocessing import Pool
from pathlib import Path
from flask import Flask, request, jsonify
import requests
from git import Repo
from llm_helper import generate_llm
import key as key_module
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SCANNER_URL = os.getenv('SCANNER_URL', 'http://scanner:8001')
MAX_WORKERS = 10  # Parallel scanning workers

def is_scannable_file(file_path: Path) -> bool:
    """Check if a file should be scanned."""
    # Skip hidden files and directories (like .git)
    return not any(part.startswith('.') for part in file_path.parts)


def scan_file(args: tuple) -> dict:
    """Send a file to the scanner service."""
    file_path, scanner_url = args
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        response = requests.post(
            f'{scanner_url}/scan',
            json={
                'filename': str(file_path),
                'content': content
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {
                'filename': str(file_path),
                'error': f'Scanner returned status {response.status_code}'
            }
    except Exception as e:
        return {
            'filename': str(file_path),
            'error': str(e)
        }

def scan_local_path(local_path: str, scanner_url: str) -> dict:
    """Scan a local directory for secrets."""
    repo_path = Path(local_path)

    if not repo_path.exists():
        raise ValueError(f"Path does not exist: {local_path}")

    if not repo_path.is_dir():
        raise ValueError(f"Path is not a directory: {local_path}")

    # Find all scannable files
    files_to_scan = [
        f for f in repo_path.rglob('*')
        if f.is_file() and is_scannable_file(f.relative_to(repo_path))
    ]

    print(f"Found {len(files_to_scan)} files to scan")

    # Scan files in parallel using multiprocessing
    scan_args = [(file_path, scanner_url) for file_path in files_to_scan]
    with Pool(processes=MAX_WORKERS) as pool:
        results = pool.map(scan_file, scan_args)

    # Aggregate results
    files_with_secrets = [r for r in results if r.get('has_secrets', False)]
    files_with_errors = sum(1 for r in results if 'error' in r)
    files_scanned = len(results) - files_with_errors

    return {
        'path': local_path,
        'summary': {
            'total_files_scanned': files_scanned,
            'files_with_secrets': len(files_with_secrets),
            'files_with_errors': files_with_errors
        },
        'findings': files_with_secrets,
        'all_results': results
    }

def clone_and_scan_repo(repo_url: str, scanner_url: str, github_token:str=None) -> dict:
    """Clone a repository and scan all files."""
    temp_dir = tempfile.mkdtemp()

    try:
        # Clone the repository
        print(f"Cloning repository: {repo_url}")
        clone_url=repo_url
        if github_token:
            if repo_url.startswith("https://github.com"):
                clone_url=repo_url.replace("https://github.com/",f"https://{github_token}@github.com/")
            elif repo_url.startswith("git@github.com:"):
                clone_url = repo_url.replace('git@github.com:', f'https://{github_token}@github.com/').replace('.git', '') + '.git'    
        
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0' 
        env['GIT_ASKPASS'] = 'echo'
        
        repo = Repo.clone_from(
            clone_url, 
            temp_dir, 
            depth=1,
            env=env
        )


        # Use the local scan function
        result = scan_local_path(temp_dir, scanner_url)
        result['repo_url'] = repo_url
        result.pop('path', None)
        return result

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    # Check if scanner is reachable
    try:
        response = requests.get(f'{SCANNER_URL}/health', timeout=5)
        scanner_healthy = response.status_code == 200
    except:
        scanner_healthy = False

    return jsonify({
        "status": "healthy" if scanner_healthy else "degraded",
        "scanner_status": "healthy" if scanner_healthy else "unhealthy"
    }), 200

@app.route('/scan-repo', methods=['POST'])
def scan_repo():
    """
    Scan a GitHub repository for secrets.

    Expected JSON body:
    {
        "repo_url": "https://github.com/user/repo.git",
        "github_token":"ghp_xxxxx" (optional)
    }
    """
    data = request.get_json()

    if not data or 'repo_url' not in data:
        return jsonify({"error": "Missing 'repo_url' field"}), 400

    repo_url = data['repo_url']
    github_token=data.get("github_token")

    # Validate URL
    if not repo_url.startswith(('https://github.com/', 'git@github.com:')):
        return jsonify({"error": "Only GitHub repositories are supported"}), 400

    try:
        results = clone_and_scan_repo(repo_url, SCANNER_URL, github_token)
        ai_result=generate_llm(results, key_module.GEMINI_KEY)
        results["ai_recommendations"]=ai_result
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/scan-local', methods=['POST'])
def scan_local():
    """
    Scan a local directory for secrets.

    Expected JSON body:
    {
        "path": "/path/to/local/directory"
    }
    """
    data = request.get_json()

    if not data or 'path' not in data:
        return jsonify({"error": "Missing 'path' field"}), 400

    local_path = data['path']

    try:
        results = scan_local_path(local_path, SCANNER_URL)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
