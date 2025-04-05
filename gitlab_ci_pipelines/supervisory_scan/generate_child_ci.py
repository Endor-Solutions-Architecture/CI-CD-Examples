import json
import yaml
import math
import os

# File paths
REPO_LIST_FILE = "repo_list.json"
DYNAMIC_PIPELINE_FILE = ".gitlab-ci.child.yml"
ENDOR_NAMESPACE = "nate-learn.gitlab"
BATCH_SIZE = 5

# Ensure repo_list.json exists
if not os.path.exists(REPO_LIST_FILE) or os.stat(REPO_LIST_FILE).st_size == 0:
    print("Error: repo_list.json does not exist or is empty!")
    exit(1)

# Load repositories
with open(REPO_LIST_FILE, "r") as f:
    repos = json.load(f)

total_repos = len(repos)
total_batches = math.ceil(total_repos / BATCH_SIZE)  # Ceiling division

print(f"Total Repositories: {total_repos}")
print(f"Total Batches: {total_batches}")

# Initialize YAML structure
pipeline = {"stages": [f"scan_batch_{i+1}" for i in range(total_batches)]}

# Generate batch jobs
for batch_index in range(total_batches):
    start = batch_index * BATCH_SIZE
    end = start + BATCH_SIZE
    batch_repos = repos[start:end]

    job_name = f"batch_{batch_index+1}"
    stage_name = f"scan_batch_{batch_index+1}"

    pipeline[job_name] = {
        "stage": stage_name,
        "image": {
            "name": "endorcipublic.azurecr.io/endorctl:latest",
            "entrypoint": [""]
        },
        "variables": {  
            "ENDOR_PNPM_ENABLED": "true",
            "ENDOR_PYTHON_PIPENV_ENABLED": "true"
        },
        "parallel": {
            "matrix": [
                {
                    "REPO_URL": [repo["repo_url"] for repo in batch_repos]
                }
            ]
        },
        "script": [
            "apt-get update && apt-get install -y curl git jq",
            "echo $REPO_URL",
            "clone_url=$(echo \"$REPO_URL\" | awk -F'[@:]' '{print $2 \"/\" $3}')",
            "echo \"clone url is:\"",
            "echo $clone_url",
            "git clone https://oauth2:$GITLAB_PAT@$clone_url",
            "repo_name=$(basename \"$REPO_URL\" .git)",
            "cd $repo_name",
            "echo \"Downloading and verifying Endorctl...\"",
            "curl  https://api.endorlabs.com/download/latest/endorctl_linux_amd64 -o endorctl",
            "echo \"Checking Endorctl SHA256 checksum...\"",
            "echo \"$(curl -s https://api.endorlabs.com/sha/latest/endorctl_linux_amd64)  endorctl\" | sha256sum -c",
            "chmod +x endorctl",
            "if [ -f pnpm-lock.yaml ] || [ -f pnpm-workspace.yaml ]; then",
            "  echo \"Detected a pnpm project. Installing pnpm & running pnpm install...\"",
            "  npm uninstall -g pnpm",
            "  npm install -g pnpm@9",
            "  pnpm install",
            "  ./endorctl scan --bypass-host-check --as-default-branch --detached-ref-name \"main\" -n \"{}\" ".format(ENDOR_NAMESPACE),
            "else",
            "  echo \"Not a pnpm project (no pnpm-lock.yaml or pnpm-workspace.yaml found). Skipping pnpm install.\"",
            "  ./endorctl scan --bypass-host-check --as-default-branch --detached-ref-name \"main\" -n \"{}\" --install-build-tools --enable-build-tools-version-detection --insecure-sandbox".format(ENDOR_NAMESPACE),
            "fi"
        ]
    }

# Write to YAML file
with open(DYNAMIC_PIPELINE_FILE, "w") as f:
    yaml.dump(pipeline, f, default_flow_style=False, sort_keys=False)

print(f"Generated child pipeline saved as {DYNAMIC_PIPELINE_FILE}")

# Ensure file exists
if not os.path.exists(DYNAMIC_PIPELINE_FILE) or os.stat(DYNAMIC_PIPELINE_FILE).st_size == 0:
    print(f"Error: {DYNAMIC_PIPELINE_FILE} was not created!")
    exit(1)
