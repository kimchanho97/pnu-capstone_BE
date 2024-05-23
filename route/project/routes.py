from flask import Blueprint, request, jsonify, make_response
from .utils import createNewProjectAndSave, getUserIdFromToken, fetchProjects, deleteProjectById, \
    getCurrentCommitMessage, getProjectDetailById
from .error import AuthorizationError
from ..models import Project, Build
from .. import db

projectBlueprint = Blueprint('project', __name__)

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


@projectBlueprint.route('/status/<projectId>', methods=['GET'])
def getProjectStatus(projectId):
    try:
        token = request.headers.get('Authorization')
        token = token.split(' ')[1]
        getUserIdFromToken(token)
        project = Project.query.filter_by(id=projectId).first()
        if project is None:
            return jsonify({'error': {'message': 'Project not found',
                                      'status': 404}}), 404

        return jsonify({'status': project.status}), 200
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
        if build:
            return jsonify({'error': {'message': 'Build already exists',
                                      'status': 4001}}), 400

        # 프로젝트 상태를 빌드 중으로 변경
        project.status = 1
        db.session.commit()

        # 현재 시간을 이용해 이미지 이름과 태그를 생성
        imageName = project.name
        imageTag = sha[:7]




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

        # 프로젝트 상태를 배포 중으로 변경
        project.status = 3
        db.session.commit()


        return make_response(jsonify({'message': 'Project deploy started successfully!'}), 200)
    except AuthorizationError as e:
        return jsonify({'error': {'message': str(e),
                                  'status': 401}}), 401
    except Exception as e:
        return jsonify({'error': {'message': 'An error occurred while deploying the project.',
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
        return jsonify({'error': {'message': 'An error occurred while building the project.',
                                  'status': 500}}), 500
