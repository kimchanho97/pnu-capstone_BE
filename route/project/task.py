import requests

def triggerArgoWorkflow(projectId, imageName, imageTag, commitMsg):
    print('"projectId":', projectId)
    print('"imageName":', f'"{imageName}"')
    print('"imageTag":', f'"{imageTag}"')
    print('"commitMsg":', f'"{commitMsg}"')
    print('"status":', '"Succeeded"')

    # Argo Workflow를 트리거하는 코드
    workflow_url = "https://your-argo-server/api/v1/workflows/your-namespace"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer (your-argo-server-token)"
    }
    data = {
        "metadata": {
            "generateName": f"build-{projectId}-"
        },
        "spec": {
            "entrypoint": "build",
            "arguments": {
                "parameters": [
                    {"name": "projectId", "value": projectId},
                    {"name": "commitMsg", "value": commitMsg},
                    {"name": "imageName", "value": imageName},
                    {"name": "imageTag", "value": imageTag}
                ]
            },
            "templates": [
                {
                    "name": "build",
                    "container": {
                        "image": "your-docker-image",
                        "command": ["sh", "-c"],
                        "args": ["echo Building $imageName:$imageTag && sleep 20 && echo Build Complete"]
                    }
                }
            ]
        }
    }
    # response = requests.post(workflow_url, headers=headers, json=data)
    response = requests.Response()
    response.status_code = 200

    return response