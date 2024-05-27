import requests, subprocess
from flask import jsonify, request
import json
import os
from .error import CreatingProjectHelmError, ArgoWorkflowError, DeployingProjectHelmError
from google.oauth2 import service_account
from googleapiclient.discovery import build


def createProjectWithHelm(release_name, envs, subdomain, github_name, github_repository, git_token, commit_sha, project_id, target_port):
    # release_name: 프로젝트 이름
    # envs: 환경 변수 {"REACT_APP_API_URL":"http://localhost:5000"}
    # subdomain: 서브도메인
    # github_name: login
    # github_repository: repository name
    # git_token: github token
    # commit_sha: commit sha[:7]
    
    if not release_name or not github_repository or not github_name:
        raise CreatingProjectHelmError("release_name, github_repository, github_name are required")
    app_release_name = release_name
    app_chart_name = "app-template"
    ci_release_name = release_name + "-ci"
    ci_chart_name = "create-projects"
    docker_token = os.environ.get("DOCKER_TOKEN")
    ci_values = {
        "fullnameOverride": ci_release_name,
        "apptemplateName": app_release_name,
        "githubName": github_name,
        "gitToken": git_token,
        "githubRepository": github_repository,
        "dockerToken": docker_token,
        "projectId": project_id
    }

    for idx, (key, value) in enumerate(envs.items()):
        ci_values[f"env[{idx}].name"] = key
        ci_values[f"env[{idx}].value"] = value

    subdomain = subdomain if subdomain else release_name
    app_values = {
        "fullnameOverride": app_release_name,
        "githubName": github_name,
        "subdomainName": subdomain,
        "dockerToken": docker_token
    }

    ci_command = [
        'helm', 'install', '-n','default',ci_release_name, ci_chart_name
    ]
    for key, value in ci_values.items():
        ci_command.extend(['--set', f"{key}={value}"])

    ci_result = subprocess.run(ci_command, capture_output=True, text=True)
    if ci_result.returncode != 0:
        raise CreatingProjectHelmError(ci_result.stderr)

    app_command = [
        'helm', 'install', '-n','default', app_release_name, app_chart_name
    ]
    for key, value in app_values.items():
        app_command.extend(['--set', f"{key}={value}"])

    app_result = subprocess.run(app_command, capture_output=True, text=True)
    if app_result.returncode != 0:
        raise CreatingProjectHelmError(app_result.stderr)

    return f"{ci_release_name}.webhook.pitapat.ne.kr", f"{subdomain}.pitapat.ne.kr"


def triggerArgoWorkflow(ci_domain, imageTag):
    # ci_domain: webHookUR
    headers = {
        "Content-Type": "application/json"
    }
    data = {"after": imageTag}
    try:
        response = requests.post("https://"+ci_domain, headers=headers, json=data)
        response.raise_for_status()  # 상태 코드가 4xx, 5xx일 경우 예외를 발생시킴
        return response
    except requests.exceptions.HTTPError as http_err:
        raise ArgoWorkflowError(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        raise ArgoWorkflowError(f"Request error occurred: {err}")


def deployWithHelm(release_name, image_tag, target_port):
    try:
        helm_chart_path = 'app-template'
        helm_upgrade_command = [
            'helm', 'upgrade', '-n', 'default', release_name, helm_chart_path, '--reuse-values',
            '--set', f'image.tag={image_tag}', '--set', f'image.repository={release_name}', '--set', f'image.targetPort={target_port}'
        ]

        result = subprocess.run(helm_upgrade_command, capture_output=True, text=True)
        if result.returncode != 0:
            raise DeployingProjectHelmError(result.stderr)

    except Exception as e:
        raise DeployingProjectHelmError(f"Error occurred: {e}")

def addDnsRecord(subdomain):
    credentials_info = json.loads(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"))
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
    MANAGED_ZONE = 'pitapat'
    dns_service = build('dns', 'v1', credentials=credentials)
    ip_address = '59.28.89.39'
    change_body = {
        "additions": [
            {
                "name": f"{subdomain}.",
                "type": "A",
                "ttl": 300,
                "rrdatas": [ip_address]
            }
        ]
    }

    request = dns_service.changes().create(
        project=PROJECT_ID,
        managedZone=MANAGED_ZONE,
        body=change_body
    )
    response = request.execute()
    return response