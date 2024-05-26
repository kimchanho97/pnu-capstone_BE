from flask import Blueprint, request, jsonify, make_response
from .utils import createNewProjectAndLogThenSave, getUserIdFromToken, fetchProjects, deleteProjectById, \
    getCurrentCommitMessage, getProjectDetailById, createBuildAndFlush, sendSseMessage, createDeployAndFlush
from .error import AuthorizationError
from ..models import Project, Build, Deploy, User, Token
from .. import db
from .task import triggerArgoWorkflow, deployWithHelm, createProjectWithHelm, CreatingProjectHelmError
from .constant import successResponse
from .error import ArgoWorkflowError, DeployingProjectHelmError

projectBlueprint = Blueprint('project', __name__)


@projectBlueprint.route('/', methods=['GET'])
def getProjects():
    try:
        token = request.headers.get('Authorization')
        token = token.split(' ')[1]
        userId = getUserIdFromToken(token)
        responseData = fetchProjects(userId)
        return make_response(jsonify(responseData), 200)
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching projects.'}), 500


@projectBlueprint.route('/<projectId>', methods=['GET'])
def getProjectDetail(projectId):
    try:
        token = request.headers.get('Authorization')
        token = token.split(' ')[1]
        getUserIdFromToken(token)
        data = getProjectDetailById(projectId)
        return make_response(jsonify(data), 200)
    except AuthorizationError as e:
        return jsonify({'error': {'message': str(e),
                                  'status': 401}}), 401
    except Exception as e:
        return jsonify({'error': {'message': 'serverError',
                                  'status': 500}}), 500


@projectBlueprint.route('/<projectId>', methods=['DELETE'])
def deleteProject(projectId):
    try:
        token = request.headers.get('Authorization')
        token = token.split(' ')[1]
        getUserIdFromToken(token)
        deleteProjectById(projectId)
        return make_response(jsonify({'message': 'Project deleted successfully!'}), 200)
    except AuthorizationError as e:
        return jsonify({'error': {'message': str(e),
                                  'status': 401}}), 401
    except Exception as e:
        return jsonify({'error': {'message': 'An error occurred while building the project.',
                                  'status': 500}}), 500


@projectBlueprint.route('/subdomain/check', methods=['GET'])
def checkSubdomain():
    try:
        subdomain = request.args.get('name')
        project = Project.query.filter_by(subdomain=subdomain).first()
        if project:
            return jsonify({'error': {'message': "이미 존재하는 SubDomain입니다.",
                                      'status': 4000}}), 400

        return make_response(jsonify(successResponse), 200)
    except Exception as e:
        return jsonify({'error': {'message': 'An error occurred while checking the subdomain.',
                                  'status': 500}}), 500


@projectBlueprint.route('/build', methods=['POST'])
def buildProject():
    try:
        token = request.headers.get('Authorization')
        token = token.split(' ')[1]
        getUserIdFromToken(token)

        projectId = request.json['id']
        project = Project.query.filter_by(id=projectId).first()
        if project is None:
            return jsonify({'error': {'message': 'Project not found',
                                      'status': 4000}}), 404

        # 프로젝트 이름과 유저 아이디를 이용해 커밋 메시지를 가져옴
        commitMsg, sha = getCurrentCommitMessage(project.name, project.user_id, token)
        print("repo_name:", project.name, ",commit_msg:", commitMsg, ",sha:", sha[:7])

        build = Build.query.filter_by(project_id=projectId, image_tag=sha[:7]).first()
        if build is not None:
            return jsonify({'error': {'message': 'Build already exists',
                                      'status': 4001}}), 400

        workflowResponse = triggerArgoWorkflow(ci_domain=project.webhook_url,
                                               imageTag=sha[:7])

        # Argo Workflow 요청이 실패하는 경우
        if workflowResponse.status_code != 200:
            project.status = 5
            db.session.commit()
            return jsonify({'error': {'message': 'Failed to trigger Argo Workflow.',
                                      'status': 500}}), 500

        # Argo Workflow 요청이 성공하는 경우 프로젝트 상태를 빌드 중으로 변경
        project.status = 1
        db.session.commit()

        sendSseMessage(f"{project.user_id}", {'projectId': projectId, 'status': project.status})

        return make_response(jsonify({'message': 'Project build started successfully!'}), 200)
    except ArgoWorkflowError as e:
        return jsonify({'error': {'message': str(e),
                                  'status': 500}}), 500
    except AuthorizationError as e:
        return jsonify({'error': {'message': str(e),
                                  'status': 401}}), 401
    except Exception as e:
        return jsonify({'error': {'message': 'An error occurred while building the project.',
                                  'status': 500}}), 500


@projectBlueprint.route('/deploy', methods=['POST'])
def deployProject():
    try:
        token = request.headers.get('Authorization')
        token = token.split(' ')[1]
        getUserIdFromToken(token)

        buildId = request.json['id']
        build = Build.query.filter_by(id=buildId).first()
        if build is None:
            return jsonify({'error': {'message': 'Build not found',
                                      'status': 4000}}), 404

        projectId = build.project_id
        project = Project.query.filter_by(id=projectId).first()

        deploy = Deploy.query.filter_by(build_id=buildId).first()
        if deploy is not None:
            return jsonify({'error': {'message': 'Deploy already exists',
                                      'status': 4001}}), 400

        # 배포 요청
        deployWithHelm(release_name=project.name, image_tag=build.image_tag)

        # 프로젝트 상태를 배포 중으로 변경
        project.status = 3
        db.session.commit()

        sendSseMessage(f"{project.user_id}", {'projectId': projectId, 'status': project.status})

        return make_response(jsonify({'message': 'Project deploy started successfully!'}), 200)
    except DeployingProjectHelmError as e:
        return jsonify({'error': {'message': str(e),
                                  'status': 500}}), 500
    except AuthorizationError as e:
        return jsonify({'error': {'message': str(e),
                                  'status': 401}}), 401
    except Exception as e:
        return jsonify({'error': {'message': 'An error occurred while deploying the project.',
                                  'status': 500}}), 500


@projectBlueprint.route('/create', methods=['POST'])
def createProject():
    try:
        token = request.headers.get('Authorization')
        token = token.split(' ')[1]
        userId = getUserIdFromToken(token)
        requestData = request.json

        user = User.query.filter_by(id=userId).first()

        name = requestData['name']
        envs = {}
        secrets = requestData['secrets']
        for secret in secrets:
            envs[secret['key']] = secret['value']
        subdomain = requestData['subdomain']
        githubName = user.login
        githubRepo = requestData['name']

        commitMsg, sha = getCurrentCommitMessage(name, userId, token)

        # 프로젝트를 먼저 DB에 생성하여 ID를 받아옴
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

        try:
            webhookUrl, domainUrl = createProjectWithHelm(release_name=name,
                                                          envs=envs,
                                                          subdomain=subdomain,
                                                          github_name=githubName,
                                                          github_repository=githubRepo,
                                                          git_token=token,
                                                          commit_sha=sha)
        except CreatingProjectHelmError as e:
            db.session.rollback()
            return jsonify({'error': {'message': str(e),
                                      'status': 500}}), 500

        # Helm 요청이 성공한 경우, URL 업데이트 및 로그 생성 후 커밋
        createNewProjectAndLogThenSave(requestData, newProject, webhookUrl, domainUrl)
        return make_response(jsonify({'message': 'Project created successfully!'}), 201)

    except AuthorizationError as e:
        return jsonify({'error': {'message': str(e),
                                  'status': 401}}), 401
    except Exception as e:
        return jsonify({'error': {'message': 'An error occurred while creating the project.',
                                  'status': 500}}), 500


@projectBlueprint.route('/build/event', methods=['POST'])
def handleArgoBuildEvent():
    try:
        data = request.json
        projectId = data['projectId']
        status = data['status']

        project = Project.query.filter_by(id=projectId).first()
        user = User.query.filter_by(id=project.user_id).first()
        token = Token.query.filter_by(user_id=user.id).first().access_token

        commitMsg, sha = getCurrentCommitMessage(project.name, project.user_id, token.access_token)

        imageName = project.name
        imageTag = sha[:7]

        project = Project.query.filter_by(id=projectId).first()

        if status == 'build-success':
            newBuildId = createBuildAndFlush(projectId, commitMsg, imageName, imageTag)
            project.status = 2  # 빌드 완료
            project.current_build_id = newBuildId
        else:
            project.status = 5  # 빌드 실패
        db.session.commit()

        sendSseMessage(f"{project.user_id}", {'projectId': projectId,
                                              'status': project.status,
                                              'currentBuildId': project.current_build_id,
                                              'currentDeployId': project.current_deploy_id})

        return make_response(jsonify({'message': 'project build success'}), 200)
    except Exception as e:
        return jsonify({'error': {'message': 'An error occurred while building the project.',
                                  'status': 500}}), 500


@projectBlueprint.route('/deploy/event', methods=['POST'])
def handleHelmWebhook():
    try:
        data = request.json
        buildId = data['buildId']
        status = data['status']

        build = Build.query.filter_by(id=buildId).first()
        project = Project.query.filter_by(id=build.project_id).first()

        if status == 'Succeeded':
            newDeployId = createDeployAndFlush(buildId)
            project.status = 4  # 배포 완료
            project.current_deploy_id = newDeployId
            project.current_build_id = buildId

            # 서브도메인 할당 및 DB에 저장

        else:
            project.status = 6  # 배포 실패

        db.session.commit()
        sendSseMessage(f"{project.user_id}", {'projectId': project.id,
                                              'status': project.status,
                                              'currentBuildId': project.current_build_id,
                                              'currentDeployId': project.current_deploy_id})

        return jsonify({'message': 'Webhook event processed successfully!'}), 200
    except Exception as e:
        return jsonify({'error': {'message': 'An error occurred while processing the webhook event.',
                                  'status': 500}}), 500
