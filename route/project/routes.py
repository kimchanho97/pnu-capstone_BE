from flask import Blueprint, request, jsonify, make_response
from .utils import createLogAndSecretsForProject, validateTokenAndGetUser, fetchProjects, deleteProjectById, \
    getCurrentCommitMessage, getProjectDetailById, createNewBuild, sendSseMessage, createNewDeploy, \
    extractToken, createNewProject, convertSecretsToDict, assignUrlsToProject, getProjectById, checkBuildExists, \
    handleWorkflowResponse, getBuildById, checkCurrentDeployId, getRolloutStatus
from ..models import Project, User, Token
from .. import db
from .task import addDnsRecord, deleteWithHelm, triggerArgoWorkflow, deployWithHelm, createProjectWithHelm, \
    deleteDnsRecord
from route.response import successResponse

projectBlueprint = Blueprint('project', __name__)

@projectBlueprint.route('/', methods=['GET'])
def getProjects():
    token = extractToken(request)
    user = validateTokenAndGetUser(token)
    responseData = fetchProjects(user.id)
    return make_response(jsonify(responseData), 200)


@projectBlueprint.route('/<projectId>', methods=['GET'])
def getProjectDetail(projectId):
    token = extractToken(request)
    validateTokenAndGetUser(token)
    responseData = getProjectDetailById(projectId)
    return make_response(jsonify(responseData), 200)


@projectBlueprint.route('/<projectId>', methods=['DELETE'])
def deleteProject(projectId):
    token = extractToken(request)
    validateTokenAndGetUser(token)
    project = getProjectById(projectId)
    deleteWithHelm(project.subdomain)
    deleteDnsRecord(project.subdomain)
    deleteDnsRecord(project.subdomain+'-ci.webhook')
    deleteProjectById(projectId)
    return make_response(jsonify(successResponse), 200)


@projectBlueprint.route('/subdomain/check', methods=['GET'])
def checkSubdomain():
    subdomain = request.args.get('name')
    project = Project.query.filter_by(subdomain=subdomain).first()
    if project:
        return jsonify({'error': {'message': "이미 존재하는 SubDomain입니다.",
                                  'status': 4000}}), 400

    return make_response(jsonify(successResponse), 200)


@projectBlueprint.route('/create', methods=['POST'])
def createProject():
    token = extractToken(request)
    user = validateTokenAndGetUser(token)
    requestData = request.json
    newProject = createNewProject(requestData, user.id)
    envs = convertSecretsToDict(requestData['secrets'])
    webhookUrl, domainUrl = createProjectWithHelm(envs=envs,
                                                  subdomain=newProject.subdomain,
                                                  github_name=user.login,
                                                  github_repository=newProject.name,
                                                  git_token=token,
                                                  project_id=newProject.id)

    addDnsRecord(webhookUrl)
    addDnsRecord(domainUrl)
    assignUrlsToProject(newProject, webhookUrl, domainUrl)
    createLogAndSecretsForProject(requestData, newProject)
    db.session.commit()
    return make_response(jsonify({"projectId": newProject.id}), 200)


@projectBlueprint.route('/build', methods=['POST'])
def buildProject():
    token = extractToken(request)
    user = validateTokenAndGetUser(token)
    project = getProjectById(request.json['id'])
    commitMsg, sha = getCurrentCommitMessage(project.name, user, token)
    checkBuildExists(project.id, sha)
    workflowResponse = triggerArgoWorkflow(ci_domain=project.webhook_url,
                                           imageTag=sha[:7])

    handleWorkflowResponse(workflowResponse, project)
    sendSseMessage(f"{project.user_id}", {'projectId': project.id, 'status': project.status})
    return make_response(jsonify(successResponse), 200)


@projectBlueprint.route('/deploy', methods=['POST'])
def deployProject():
    token = extractToken(request)
    validateTokenAndGetUser(token)
    build = getBuildById(request.json['id'])
    project = getProjectById(build.project_id)
    checkCurrentDeployId(build.id, project.current_deploy_id)
    deployWithHelm(subdomain=project.subdomain, image_tag=build.image_tag, target_port=project.port)

    project.status = 3  # 배포 중
    db.session.commit()
    sendSseMessage(f"{project.user_id}", {'projectId': project.id, 'status': project.status})
    return make_response(jsonify(successResponse), 200)


@projectBlueprint.route('/build/event', methods=['POST'])
def handleArgoBuildEvent():
    data = request.json
    project = Project.query.filter_by(id=data['projectId']).first()
    user = User.query.filter_by(id=project.user_id).first()
    token = Token.query.filter_by(user_id=user.id).first()
    commitMsg, sha = getCurrentCommitMessage(project.name, user, token.access_token)

    status = data['status']
    if status == 'build-success':
        newBuild = createNewBuild(project.id, commitMsg, project.name, sha[:7])
        project.status = 2  # 빌드 완료
        project.current_build_id = newBuild.id
    else:
        project.status = 5  # 빌드 실패

    # 빌드 로그를 업데이트하는 작업이 필요함

    db.session.commit()
    sendSseMessage(f"{project.user_id}", {'projectId': project.id,
                                          'status': project.status,
                                          'currentBuildId': project.current_build_id,
                                          'currentDeployId': project.current_deploy_id})
    return make_response(jsonify(successResponse), 200)


@projectBlueprint.route('/deploy/status', methods=['GET'])
def checkDeployStatus():
    token = extractToken(request)
    validateTokenAndGetUser(token)
    buildId = request.args.get('buildId')
    build = getBuildById(buildId)
    project = getProjectById(build.project_id)
    status = getRolloutStatus(project.subdomain)

    if status in ['Healthy', 'Degraded', 'InvalidSpec']:
        if status == 'Healthy':
            newDeploy = createNewDeploy(build.id)
            project.status = 4  # 배포 완료
            project.current_deploy_id = newDeploy.id
            project.current_build_id = build.id
        else:
            project.status = 6  # 배포 실패

        # 배포 로그를 업데이트하는 작업이 필요함

        db.session.commit()
        sendSseMessage(f"{project.user_id}", {'projectId': project.id,
                                              'status': project.status,
                                              'currentBuildId': project.current_build_id,
                                              'currentDeployId': project.current_deploy_id})

    return make_response(jsonify(successResponse), 200)