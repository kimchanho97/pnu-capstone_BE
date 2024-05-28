from .login import userBlueprint
from sqlalchemy.exc import SQLAlchemyError
from .. import db
from flask import jsonify


@userBlueprint.errorhandler(SQLAlchemyError)
def handleDatabaseError():
    db.session.rollback()
    return jsonify({'error': {'message': 'Database Error',
                              'status': 500}}), 500


@userBlueprint.errorhandler(Exception)
def handleServerError():
    return jsonify({'error': {'message': 'Server Error',
                              'status': 500}}), 500
