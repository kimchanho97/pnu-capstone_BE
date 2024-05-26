from .. import db
from ..models import Project, Secret, Token, User, Build, Deploy, Log
import requests
from sqlalchemy.exc import SQLAlchemyError
from .error import AuthorizationError
from flask_sse import sse


def sendSseMessage(channel, message):
    sse.publish(message, type='message', channel=channel)


def getProjectDetailById(projectId):
    try:
        # 프로젝트 아이디를 이용해 프로젝트 정보를 가져와 반환
        data = {'builds': [], 'deploys': [], 'secrets': [], 'domainUrl': '', 'webhookUrl': '', 'subdomain': ''}
        project = Project.query.filter_by(id=projectId).first()
        if project is None:
            raise Exception('Project not found')

        builds = Build.query.filter_by(project_id=projectId).all()
        for build in builds:
            data['builds'].append({
                'id': build.id,
                'buildDate': build.build_date,
                'commitMsg': build.commit_msg,
                'imageTag': build.image_tag
            })

            deploy = Deploy.query.filter_by(build_id=build.id).first()
            if deploy is not None:
                data['deploys'].append({
                    'id': deploy.id,
                    'buildId': deploy.build_id,
                    'deployDate': deploy.deploy_date,
                    'commitMsg': build.commit_msg,
                    'imageTag': build.image_tag
                })

        data['domainUrl'] = project.domain_url
        data['webhookUrl'] = project.webhook_url
        data['subdomain'] = project.subdomain

        secrets = Secret.query.filter_by(project_id=projectId).all()
        for secret in secrets:
            data['secrets'].append({
                'key': secret.key,
                'value': secret.value
            })

        return data
    except SQLAlchemyError as e:
        print(f"Database Error: {e}")
        raise Exception('An error occurred while fetching project detail')


def createBuildAndFlush(projectId, commitMsg, imageName, imageTag):
    # 빌드 정보를 저장
    newBuild = Build(
        project_id=projectId,
        commit_msg=commitMsg,
        image_name=imageName,
        image_tag=imageTag
    )
    db.session.add(newBuild)
    db.session.flush()

    return newBuild.id

def createDeployAndFlush(buildId):
    # 배포 정보를 저장
    newDeploy = Deploy(
        build_id=buildId
    )
    db.session.add(newDeploy)
    db.session.flush()

    return newDeploy.id

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
    try:
        # 프로젝트 아이디를 이용해 프로젝트를 삭제
        project = Project.query.filter_by(id=projectId).first()
        if project is None:
            raise Exception('Project not found')

        project.current_build_id = None
        project.current_deploy_id = None

        db.session.delete(project)
        db.session.commit()
        return
    except SQLAlchemyError as e:
        print(f"Database Error: {e}")
        raise Exception('An error occurred while deleting project')

def fetchProjects(userId):
    try:
        # 유저 아이디를 이용해 프로젝트 리스트를 가져와 반환
        projects = Project.query.filter_by(user_id=userId).all()
        projectList = []
        for project in projects:
            projectList.append({
                'id': project.id,
                'name': project.name,
                'status': project.status,
                'framework': project.framework,
                'currentBuildId': project.current_build_id,
                'currentDeployId': project.current_deploy_id
            })
        return projectList
    except SQLAlchemyError as e:
        raise Exception('Database Error: An error occurred while fetching projects')

def getUserIdFromToken(token):
    try:
        # 토큰을 이용해 유저 아이디를 찾아 반환
        if token is None:
            raise AuthorizationError('Authorization header is required')

        tokenEntry = Token.query.filter_by(access_token=token).first()
        if tokenEntry is None:
            raise AuthorizationError('Invalid token')
        return tokenEntry.user_id
    except SQLAlchemyError as e:
        print(f"Database Error: {e}")
        raise Exception('An error occurred while fetching user id from token')

def createNewProjectAndLogThenSave(requestData, newProject, webhookUrl, domainUrl):
    try:
        print("requestData = ", requestData)
        newProject.webhook_url = webhookUrl
        newProject.domain_url = domainUrl

        newLog = Log(
            project_id=newProject.id,
            build_log='',
            deploy_log=''
        )
        db.session.add(newLog)

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
        raise Exception('An error occurred while creating new project')