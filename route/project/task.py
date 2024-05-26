import requests, subprocess
import jsonify
import os

def createProjectWithHelm(release_name, envs={}, subdomain=None, github_name, github_repository, git_token, commit_sha):
    if not release_name or not github_repository or not github_name:
        return jsonify({"error": "release_name and github info are required"}), 400
    app_release_name = release_name
    app_chart_name = "./app-template"
    ci_release_name = release_name+"-ci"
    ci_chart_name = "./create-projects"
    docker_token = os.environ.get("DOCKER_TOKEN")
    ci_values = {
        "fullnameOverride": ci_chart_name,
        "apptemplateName": app_chart_name,
        "githubName": github_name,
        "gitToken": git_token,
        "githubRepository": github_repository,
        "dockerToken": docker_token
        }
    for idx, (key, value) in enumerate(envs.items()):
        ci_values[f"env[{idx}].name"] = key
        ci_values[f"env[{idx}].value"] = value

    subdomain = subdomain if subdomain else release_name
    app_values = {
        "fullnameOverride": app_chart_name,
        "image.tag": commit_sha[0:7],
        "image.repository": app_chart_name,
        "githubName": github_name,
        "subdomainName": subdomain,
        "dockerToken": docker_token
    }

    try:
        ci_command = [
            'helm', 'install', ci_release_name, ci_chart_name
        ]
        for key, value in ci_values.items():
            ci_command.extend(['--set', f"{key}={value}"])
        ci_result = subprocess.run(command, capture_output=True, text=True)
        if ci_result.returncode != 0:
            return jsonify({"error": ci_result.stderr}), 500

        app_command = [
            'helm', 'install', app_release_name, app_chart_name
        ]
        for key, value in app_values.items():
            app_command.extend(['--set', f"{key}={value}"])
        app_result = subprocess.run(command, capture_output=True, text=True)
        if app_result.returncode != 0:
            return jsonify({"error": app_result.stderr}), 500

        return jsonify({
            "release_name": release_name,
            "message": "created",
            "output": ci_result.stdout+app_result.stdout,
            "ci_domain": f"{ci_release_name}.webhook.pitapat.ne.kr",
            "app_domain": f"{subdomain}.pitapat.ne.kr"
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def triggerArgoWorkflow(ci_domain, imageTag):
    headers = {
        "Content-Type": "application/json"
    }
    data = {"after": imageTag}
    try:
        response = requests.post(ci_domain, headers=headers, json=data)
        response.raise_for_status()  # 상태 코드가 4xx, 5xx일 경우 예외를 발생시킴
        return response.json(), response.status_code
    except requests.exceptions.HTTPError as http_err:
        return {"error": str(http_err)}, response.status_code
    except requests.exceptions.RequestException as err:
        return {"error": str(err)}, 500


def deployWithHelm(release_name, image_tag):
    print('"buildId":', buildId)
    print('"status":', '"Succeeded"')
    helm_chart_path = './app-template'
    helm_upgrade_command = [
        'helm', 'upgrade', release_name, helm_chart_path, '--reuse-values',
        '--set', f'image.tag={image_tag}'
    ]

    try:
        result = subprocess.run(helm_upgrade_command, capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({"error": result.stderr}), 500
        return jsonify({
            "release_name": release_name,
            "message": "deployed",
            "output": result.stdout
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500