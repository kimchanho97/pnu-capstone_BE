from .. import db
from ..models import Project, Secret, Token

class AuthorizationError(Exception):
    pass

def fetchProjects(userId):
    # 유저 아이디를 이용해 프로젝트 리스트를 가져와 반환
    projects = Project.query.filter_by(user_id=userId).all()
    projectList = []
    for project in projects:
        projectList.append({
            'id': project.id,
            'name': project.name,
            'status': project.status,
            'framework': project.framework,
        })
    return projectList

def getUserIdFromToken(token):
    # 토큰을 이용해 유저 아이디를 찾아 반환
    if token is None:
        raise AuthorizationError('Authorization header is required')

    tokenEntry = Token.query.filter_by(access_token=token).first()
    if tokenEntry is None:
        raise AuthorizationError('Invalid token')
    return tokenEntry.user_id

def createNewProjectAndSave(requestData, userId):
    try:
        print("requestData = ", requestData)
        port = int(requestData['port']) if requestData['port'] else None
        minReplicas = int(requestData['minReplicas']) if requestData['minReplicas'] else None
        maxReplicas = int(requestData['maxReplicas']) if requestData['maxReplicas'] else None
        cpuThreshold = int(requestData['cpuThreshold']) if requestData['cpuThreshold'] else None

        newProject = Project(
            user_id=userId,
            name=requestData['name'],
            framework=requestData['framework'],
            port=port,
            auto_scaling=requestData['autoScaling'],
            min_replicas=minReplicas,
            max_replicas=maxReplicas,
            cpu_threshold=cpuThreshold,
        )
        db.session.add(newProject)
        db.session.flush()

        if len(requestData['secrets']) > 0:
            for secret in requestData['secrets']:
                newSecret = Secret(
                    project_id=newProject.id,
                    key=secret['key'],
                    value=secret['value']
                )
                db.session.add(newSecret)

        # 모든 작업을 성공적으로 마치면 commit
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

    return