from .. import db
from ..models import Project, Secret, Token, User, Build
import requests

class AuthorizationError(Exception):
    pass

def createBuildAndSave(projectId, commitMsg, imageName, imageTag):
    # 빌드 정보를 저장
    newBuild = Build(
        project_id=projectId,
        commit_msg=commitMsg,
        image_name=imageName,
        image_tag=imageTag
    )
    db.session.add(newBuild)
    db.session.commit()
    return

def getCurrentCommitMessage(projectName, userId, token):
    user = User.query.filter_by(id=userId).first()
    login = user.login
    # 프로젝트 이름과 유저 이름을 이용해 커밋 메시지를 가져와 반환
    repoUrl = f'https://api.github.com/repos/{login}/{projectName}/commits?per_page=1'

    # 헤더에 토큰을 추가
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json',
    }

    response = requests.get(repoUrl, headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to fetch commit message')

    commitMsg = response.json()[0]['commit']['message']
    sha = response.json()[0]['sha']
    return commitMsg, sha

def deleteProjectById(projectId):
    # 프로젝트 아이디를 이용해 프로젝트를 삭제
    project = Project.query.filter_by(id=projectId).first()
    if project is None:
        raise Exception('Project not found')
    db.session.delete(project)
    db.session.commit()
    return

def fetchProjects(userId):
    # 유저 아이디를 이용해 프로젝트 리스트를 가져와 반환
    projects = Project.query.filter_by(user_id=userId).all()
    projectList = []
    for project in projects:
        projectList.append({
            'id': project.id,
            'name': project.name,
            'status': project.status,
            'framework': project.framework,
        })
    return projectList

def getUserIdFromToken(token):
    # 토큰을 이용해 유저 아이디를 찾아 반환
    if token is None:
        raise AuthorizationError('Authorization header is required')

    tokenEntry = Token.query.filter_by(access_token=token).first()
    if tokenEntry is None:
        raise AuthorizationError('Invalid token')
    return tokenEntry.user_id

def createNewProjectAndSave(requestData, userId):
    try:
        print("requestData = ", requestData)
        port = int(requestData['port']) if requestData['port'] else None
        minReplicas = int(requestData['minReplicas']) if requestData['minReplicas'] else None
        maxReplicas = int(requestData['maxReplicas']) if requestData['maxReplicas'] else None
        cpuThreshold = int(requestData['cpuThreshold']) if requestData['cpuThreshold'] else None

        newProject = Project(
            user_id=userId,
            name=requestData['name'],
            framework=requestData['framework'],
            port=port,
            auto_scaling=requestData['autoScaling'],
            min_replicas=minReplicas,
            max_replicas=maxReplicas,
            cpu_threshold=cpuThreshold,
        )
        db.session.add(newProject)
        db.session.flush()

        if len(requestData['secrets']) > 0:
            for secret in requestData['secrets']:
                newSecret = Secret(
                    project_id=newProject.id,
                    key=secret['key'],
                    value=secret['value']
                )
                db.session.add(newSecret)

        # 모든 작업을 성공적으로 마치면 commit
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

    return