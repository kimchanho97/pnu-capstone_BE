from flask import Blueprint, request, jsonify, make_response
from .utils import createNewProjectAndSave, getUserIdFromToken, AuthorizationError, fetchProjects

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
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': 'An error occurred while creating the project.'}), 500





