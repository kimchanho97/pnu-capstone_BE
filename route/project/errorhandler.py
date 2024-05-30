from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
from route.project.error import AuthorizationError, DeletingProjectHelmError, ProjectNotFoundError, CreatingProjectHelmError, ArgoWorkflowError, \
    DeployingProjectHelmError, BuildExistsError, BuildNotFoundError, DeployExistsError
from .routes import projectBlueprint
from .. import db


@projectBlueprint.errorhandler(AuthorizationError)
def handleAuthorizationError(error):
    return jsonify({'error': {'message': str(error),
                              'status': 401}}), 401


@projectBlueprint.errorhandler(ProjectNotFoundError)
def handleProjectNotFoundError(error):
    return jsonify({'error': {'message': str(error),
                              'status': 404}}), 404


@projectBlueprint.errorhandler(CreatingProjectHelmError)
def handleCreatingProjectHelmError(error):
    return jsonify({'error': {'message': str(error),
                              'status': 500}}), 500


@projectBlueprint.errorhandler(BuildExistsError)
def handleBuildExistsError(error):
    return jsonify({'error': {'message': str(error),
                              'status': 4001}}), 400


@projectBlueprint.errorhandler(ArgoWorkflowError)
def handleArgoWorkflowError(error):
    return jsonify({'error': {'message': str(error),
                              'status': 500}}), 500


@projectBlueprint.errorhandler(BuildNotFoundError)
def handleBuildNotFoundError(error):
    return jsonify({'error': {'message': str(error),
                              'status': 404}}), 404


@projectBlueprint.errorhandler(DeployExistsError)
def handleDeployExistsError(error):
    return jsonify({'error': {'message': str(error),
                              'status': 4001}}), 400


@projectBlueprint.errorhandler(DeployingProjectHelmError)
def handleDeployingProjectHelmError(error):
    return jsonify({'error': {'message': str(error),
                              'status': 500}}), 500

@projectBlueprint.errorhandler(DeletingProjectHelmError)
def handleDeletingProjectHelmError(error):
    return jsonify({'error': {'message': str(error),
                              'status': 500}}), 500




@projectBlueprint.errorhandler(SQLAlchemyError)
def handleDatabaseError():
    db.session.rollback()
    return jsonify({'error': {'message': 'Database Error',
                              'status': 500}}), 500


@projectBlueprint.errorhandler(Exception)
def handleServerError():
    return jsonify({'error': {'message': 'Server Error',
                              'status': 500}}), 500
