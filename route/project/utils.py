import requests

from .. import db
from ..models import Project, Secret, Token, User, Build, Deploy, Log
from sqlalchemy.exc import SQLAlchemyError
from route.project.error import AuthorizationError, ProjectNotFoundError, BuildExistsError, ArgoWorkflowError, \
    BuildNotFoundError, DeployExistsError
from flask_sse import sse


def sendSseMessage(channel, message):
    sse.publish(message, type='message', channel=channel)


def extractToken(request):
    token = request.headers.get('Authorization')
    if token is None:
        raise AuthorizationError('Authorization token is required')
    return token.split(' ')[1]


def validateTokenAndGetUser(token):
    try:
        tokenEntry = Token.query.filter_by(access_token=token).first()
        if tokenEntry is None:
            raise AuthorizationError('Invalid token')
        user = User.query.filter_by(id=tokenEntry.user_id).first()
        return user
    except SQLAlchemyError as e:
        raise e


def fetchProjects(userId):
    try:
        projects = Project.query.filter_by(user_id=userId).all()
        projectList = []
        for project in projects:
            projectList.append({
                'id': project.id,
                'name': project.name,
                'status': project.status,
                'framework': project.framework,
                'currentBuildId': project.current_build_id,
                'currentDeployId': project.current_deploy_id,
                'description': project.description
            })
        return projectList
    except SQLAlchemyError as e:
        raise e


def getProjectDetailById(projectId):
    try:
        data = {'builds': [], 'deploys': [], 'secrets': [], 'domainUrl': '', 'webhookUrl': '', 'subdomain': '',
                'detailedDescription': ''}
        project = Project.query.filter_by(id=projectId).first()
        if project is None:
            raise ProjectNotFoundError('Project not found')

        builds = Build.query.filter_by(project_id=projectId).all()
        for build in builds:
            data['builds'].append({
                'id': build.id,
                'buildDate': build.build_date,
                'commitMsg': build.commit_msg,
                'imageTag': build.image_tag
            })
            deploys = Deploy.query.filter_by(build_id=build.id).all()
            for deploy in deploys:
                data['deploys'].append({
                    'id': deploy.id,
                    'buildId': deploy.build_id,
                    'deployDate': deploy.deploy_date,
                    'commitMsg': build.commit_msg,
                    'imageTag': build.image_tag
                })
        data['deploys'].sort(key=lambda x: x['id'])

        data['domainUrl'] = project.domain_url
        data['webhookUrl'] = project.webhook_url
        data['subdomain'] = project.subdomain
        data['detailedDescription'] = project.detailed_description

        secrets = Secret.query.filter_by(project_id=projectId).all()
        for secret in secrets:
            data['secrets'].append({
                'key': secret.key,
                'value': secret.value
            })

        return data
    except SQLAlchemyError as e:
        raise e


def deleteProjectById(projectId):
    try:
        project = Project.query.filter_by(id=projectId).first()
        if project is None:
            raise ProjectNotFoundError('Project not found')


        project.current_build_id = None
        project.current_deploy_id = None

        deploys = Deploy.query.filter_by(project_id=projectId).all()
        for deploy in deploys:
            deploy.build_id = None

        # Project 레코드 삭제
        db.session.delete(project)
        db.session.commit()
    except SQLAlchemyError as e:
        raise e


def createNewProject(requestData, userId):
    try:
        newProject = Project(
            user_id=userId,
            name=requestData['name'],
            framework=requestData['framework'],
            port=int(requestData['port']) if requestData['port'] else None,
            auto_scaling=requestData['autoScaling'],
            min_replicas=int(requestData['minReplicas']) if requestData['minReplicas'] else None,
            max_replicas=int(requestData['maxReplicas']) if requestData['maxReplicas'] else None,
            cpu_threshold=int(requestData['cpuThreshold']) if requestData['cpuThreshold'] else None,
            subdomain=requestData['subdomain']
        )
        db.session.add(newProject)
        db.session.flush()
        return newProject
    except SQLAlchemyError as e:
        raise e


def convertSecretsToDict(secrets):
    secretDict = {}
    for secret in secrets:
        secretDict[secret['key']] = secret['value']
    return secretDict


def getCurrentCommitMessage(projectName, user, token):
    repoUrl = f'https://api.github.com/repos/{user.login}/{projectName}/commits?per_page=1'
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    response = requests.get(repoUrl, headers=headers)
    if response.status_code != 200:
        raise AuthorizationError('Token is expired')

    commitMsg = response.json()[0]['commit']['message']
    sha = response.json()[0]['sha']
    return commitMsg, sha


def assignUrlsToProject(project, webhookUrl, domainUrl):
    project.webhook_url = webhookUrl
    project.domain_url = domainUrl


def createLogAndSecretsForProject(requestData, newProject):
    try:
        newLog = Log(
            project_id=newProject.id,
            build_log='',
            deploy_log=''
        )
        db.session.add(newLog)

        for secret in requestData['secrets']:
            newSecret = Secret(
                project_id=newProject.id,
                key=secret['key'],
                value=secret['value']
            )
            db.session.add(newSecret)

    except SQLAlchemyError as e:
        raise e


def getProjectById(projectId):
    project = Project.query.filter_by(id=projectId).first()
    if project is None:
        raise ProjectNotFoundError('Project not found')
    return project


def checkBuildExists(projectId, imageTag):
    build = Build.query.filter_by(project_id=projectId, image_tag=imageTag).first()
    if build is not None:
        raise BuildExistsError('Build already exists')


def handleWorkflowResponse(response, project):
    # Argo Workflow 요청이 실패하는 경우
    if response.status_code != 200:
        project.status = 5  # 빌드 실패
        db.session.commit()
        raise ArgoWorkflowError('Argo Workflow request failed')

    # Argo Workflow 요청이 성공하는 경우
    else:
        project.status = 1  # 빌드 중
        db.session.commit()


def getBuildById(buildId):
    build = Build.query.filter_by(id=buildId).first()
    if build is None:
        raise BuildNotFoundError('Build not found')
    return build


def checkCurrentDeployId(buildId, currentDeployId):
    deploy = Deploy.query.filter_by(build_id=buildId).order_by(Deploy.id.desc()).first()
    if deploy:
        if currentDeployId == deploy.id:
            raise DeployExistsError('Deploy already exists')


def createNewBuild(projectId, commitMsg, imageName, imageTag):
    # 빌드 정보를 저장
    newBuild = Build(
        project_id=projectId,
        commit_msg=commitMsg,
        image_name=imageName,
        image_tag=imageTag
    )
    db.session.add(newBuild)
    db.session.flush()
    return newBuild


def getRolloutStatus(subdomain):
    return "Healthy"
    response = requests.get(
        f'http://argo-rollouts-dashboard.argo-rollouts.svc.cluster.local:3100/api/v1/rollouts/{subdomain}/{subdomain}/info',
        headers={'Content-Type': 'application/json'})
    responseData = response.json()
    status = responseData['status']
    return "Healthy"


def createNewDeploy(buildId, projectId):
    newDeploy = Deploy(
        build_id=buildId,
    )
    db.session.add(newDeploy)
    db.session.flush()
    return newDeploy