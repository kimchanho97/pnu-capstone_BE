from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
from route.project.error import AuthorizationError, DeletingProjectHelmError, ProjectNotFoundError, CreatingProjectHelmError, ArgoWorkflowError, \
    DeployingProjectHelmError, BuildExistsError, BuildNotFoundError, DeployExistsError
from .. import db

def registerProjectErrorHandler(app):
    @app.errorhandler(AuthorizationError)
    def handleAuthorizationError(error):
        return jsonify({'error': {'message': str(error),
                                  'status': 401}}), 401

    @app.errorhandler(ProjectNotFoundError)
    def handleProjectNotFoundError(error):
        return jsonify({'error': {'message': str(error),
                                  'status': 404}}), 404

    @app.errorhandler(CreatingProjectHelmError)
    def handleCreatingProjectHelmError(error):
        return jsonify({'error': {'message': str(error),
                                  'status': 500}}), 500

    @app.errorhandler(BuildExistsError)
    def handleBuildExistsError(error):
        return jsonify({'error': {'message': str(error),
                                  'status': 4001}}), 400

    @app.errorhandler(ArgoWorkflowError)
    def handleArgoWorkflowError(error):
        return jsonify({'error': {'message': str(error),
                                  'status': 500}}), 500

    @app.errorhandler(BuildNotFoundError)
    def handleBuildNotFoundError(error):
        return jsonify({'error': {'message': str(error),
                                  'status': 404}}), 404

    @app.errorhandler(DeployExistsError)
    def handleDeployExistsError(error):
        return jsonify({'error': {'message': str(error),
                                  'status': 4001}}), 400

    @app.errorhandler(DeployingProjectHelmError)
    def handleDeployingProjectHelmError(error):
        return jsonify({'error': {'message': str(error),
                                  'status': 500}}), 500

    @app.errorhandler(DeletingProjectHelmError)
    def handleDeletingProjectHelmError(error):
        return jsonify({'error': {'message': str(error),
                                  'status': 500}}), 500

    @app.errorhandler(SQLAlchemyError)
    def handleDatabaseError(error):
        db.session.rollback()
        return jsonify({'error': {'message': str(error),
                                  'status': 500}}), 500

    @app.errorhandler(Exception)
    def handleServerError(error):
        return jsonify({'error': {'message': str(error),
                                  'status': 500}}), 500
