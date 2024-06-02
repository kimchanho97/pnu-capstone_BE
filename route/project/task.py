import requests, subprocess
import json
import os

from route.project.error import CreatingProjectHelmError, ArgoWorkflowError, DeletingProjectHelmError, DeployingProjectHelmError
from google.oauth2 import service_account
from googleapiclient.discovery import build


def createProjectWithHelm(envs, subdomain, github_name, github_repository, git_token, project_id):
    app_release_name = subdomain
    app_chart_name = "app-template"
    ci_release_name = subdomain + "-ci"
    ci_chart_name = "create-projects"
    return f"{ci_release_name}.webhook.pitapat.ne.kr", f"{subdomain}.pitapat.ne.kr"
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

    app_values = {
        "fullnameOverride": app_release_name,
        "githubName": github_name,
        "subdomainName": subdomain,
        "dockerToken": docker_token
    }
    try:
        ci_command = [
            'helm', 'install', '-n', 'default', ci_release_name, ci_chart_name
        ]
        for key, value in ci_values.items():
            ci_command.extend(['--set', f"{key}={value}"])

        ci_result = subprocess.run(ci_command, capture_output=True, text=True)
        ci_result.check_returncode()

        app_command = [
            'helm', 'install', '-n','default', app_release_name, app_chart_name
        ]
        for key, value in app_values.items():
            app_command.extend(['--set', f"{key}={value}"])

        app_result = subprocess.run(app_command, capture_output=True, text=True)
        app_result.check_returncode()

        return f"{ci_release_name}.webhook.pitapat.ne.kr", f"{subdomain}.pitapat.ne.kr"

    except subprocess.CalledProcessError as e:
        raise CreatingProjectHelmError(f"Helm command failed: {e.stderr}")
    except Exception as e:
        raise CreatingProjectHelmError(f"Unexpected error: {e}")


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


def deployWithHelm(subdomain, image_tag, target_port):
    try:
        helm_chart_path = 'app-template'
        helm_upgrade_command = [
            'helm', 'upgrade', '-n', 'default', subdomain, helm_chart_path, '--reuse-values',
            '--set', f'image.tag={image_tag}', '--set', f'image.repository={subdomain}', '--set', f'image.targetPort={target_port}'
        ]

        result = subprocess.run(helm_upgrade_command, capture_output=True, text=True)
        if result.returncode != 0:
            raise DeployingProjectHelmError(result.stderr)

    except Exception as e:
        raise DeployingProjectHelmError(f"Unexpected error: {e}")


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

def deleteWithHelm(subdomain):
    try:
        helm_delete_command = [
            'helm', 'delete', '-n', 'default', subdomain
        ]
        result = subprocess.run(helm_delete_command, capture_output=True, text=True)
        if result.returncode != 0:
            raise DeletingProjectHelmError(result.stderr)
        helm_ci_delete_command = [
            'helm', 'delete', '-n', 'default', subdomain+'-ci'
        ]
        result = subprocess.run(helm_ci_delete_command, capture_output=True, text=True)
        if result.returncode != 0:
            raise DeletingProjectHelmError(result.stderr)

    except Exception as e:
        raise DeletingProjectHelmError(f"Unexpected error: {e}")

def deleteDnsRecord(domain):
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
        "deletions": [
            {
                "name": f"{domain}.pitapat.ne.kr.",
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

def fetchBuildLogs(subdomain):
    url = f"https://argo-server.argo.svc.cluster.local:2746/api/v1/workflows/{subdomain}-ci2"
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 에러가 발생했는지 확인
        build_data = response.json()
        build_log = ""

        if 'items' in build_data and len(build_data['items']) > 0:
            # 최근 빌드 식별자 추출
            recent_build = build_data['items'][0]
            recent_build_id = recent_build['metadata']['name']

            # 빌드 로그 추출
            build_logs = recent_build.get('spec', {}).get('templates', [])
            for log in build_logs:
                build_log += f"Template Name: {log['name']}\n"
                if 'container' in log:
                    build_log += f"Container Image: {log['container'].get('image', 'N/A')}\n"
                    build_log += f"Container Args: {log['container'].get('args', 'N/A')}\n"
                if 'inputs' in log:
                    build_log += f"Inputs: {log['inputs']}\n"
                if 'outputs' in log:
                    build_log += f"Outputs: {log['outputs']}\n"

        return build_log
    except requests.exceptions.HTTPError as http_err:
        raise Exception(f"HTTP error occurred: {http_err}")
    except Exception as err:
        raise Exception(f"An error occurred: {err}")
