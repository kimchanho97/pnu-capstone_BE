from .login import userBlueprint
from sqlalchemy.exc import SQLAlchemyError
from .. import db
from flask import jsonify

def registerUserErrorHandler(app):
    @app.errorhandler(SQLAlchemyError)
    def handleDatabaseError():
        db.session.rollback()
        return jsonify({'error': {'message': 'Database Error',
                                  'status': 500}}), 500

    @app.errorhandler(Exception)
    def handleServerError():
        return jsonify({'error': {'message': 'Server Error',
                                  'status': 500}}), 500
