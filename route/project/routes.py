from flask import Blueprint, request, jsonify, make_response
from .utils import createNewProjectAndSave, getUserIdFromToken, fetchProjects, deleteProjectById, \
    getCurrentCommitMessage, getProjectDetailById, createBuildAndFlush, sendSseMessage, createDeployAndFlush
from .error import AuthorizationError
from ..models import Project, Build, Deploy
from .. import db
from .task import triggerArgoWorkflow, deployWithHelm

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

        imageName = project.name
        imageTag = sha[:7]

        workflowResponse = triggerArgoWorkflow(projectId, imageName, imageTag, commitMsg)
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
        success, errorMessage = deployWithHelm(buildId, build.image_name, build.image_tag)
        if not success:
            project.status = 6  # 배포 실패 상태
            db.session.commit()
            return jsonify({'error': {'message': 'Helm command failed: ' + errorMessage,
                                      'status': 500}}), 500

        # 프로젝트 상태를 배포 중으로 변경
        project.status = 3
        db.session.commit()

        sendSseMessage(f"{project.user_id}", {'projectId': projectId, 'status': project.status})

        return make_response(jsonify({'message': 'Project deploy started successfully!'}), 200)
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
        createNewProjectAndSave(requestData, userId)
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
        imageName = data['imageName']
        imageTag = data['imageTag']
        commitMsg = data['commitMsg']
        status = data['status']

        project = Project.query.filter_by(id=projectId).first()

        if status == 'Succeeded':
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