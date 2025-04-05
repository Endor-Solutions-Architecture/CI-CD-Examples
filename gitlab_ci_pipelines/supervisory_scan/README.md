# Security Supervisor

An example supervisory job for running batch scanning of `endorctl` against a GitLab group. This project is designed to automate the process of fetching, processing, and scanning repositories within a specified GitLab group.

## Pipeline Overview

The CI/CD pipeline consists of the following stages:

1. **Fetch Repositories**: Retrieves repositories from the specified GitLab group that have been updated since the last run.
2. **Process Repositories**: Clones the repositories and categorizes them by programming language (PHP, Ruby, Other).
3. **Run Scans**: Executes language-specific scans using `endorctl` for PHP, Ruby, and other categorized repositories.

## Required Environment Variables

The following environment variables need to be configured in your GitLab CI/CD settings:

| Variable | Description | Required | Default |
|----------|-------------|-----------|---------|
| `GITLAB_TOKEN` | Private token for GitLab API access | Yes | - |
| `GITLAB_GROUP` | Name of the GitLab group to scan | Yes | - |
| `GITLAB_API_URL` | GitLab API endpoint URL | No | `https://gitlab.com/api/v4` |
| `BATCH_SIZE` | Number of repositories to process per job | No | `5` |
| `ENDOR_API_CREDENTIALS_KEY` | API key for Endor authentication | Yes | - |
| `ENDOR_API_CREDENTIALS_SECRET` | API secret for Endor authentication | Yes | - |

### Setting up Environment Variables

1. Go to your GitLab project's **Settings > CI/CD**
2. Expand the **Variables** section
3. Click **Add Variable** and add each of the required variables
4. For sensitive variables like `GITLAB_TOKEN`, `ENDOR_API_CREDENTIALS_KEY`, and `ENDOR_API_CREDENTIALS_SECRET`, make sure to mark them as **Masked** and **Protected** if appropriate

## Runner Requirements

The pipeline requires runners with the following:
- Tag: `parallel-runner`
- Ability to run Docker containers
- Sufficient permissions to clone repositories

## Usage

1. **Configure Environment Variables**: Ensure all required environment variables are set in your GitLab project settings.
2. **Run the Pipeline**: Trigger the pipeline manually or set it to run on a schedule.
3. **Monitor Results**: Check the pipeline logs and artifacts for results of the scans.

## Notes

- The `awk` command is used to distribute repositories across parallel jobs.
- The `endorctl` tool is downloaded and executed within each repository to perform security scans.
- Ensure that the `endorctl` tool and its dependencies are correctly configured and accessible.