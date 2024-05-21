import time
from .utils import createBuildAndSave
from .. import db
from ..models import Project

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
from app import celery

@celery.task(name='route.project.task.buildProjectTask')
def buildProjectTask(projectId, commitMsg, imageName, imageTag):
    # 실제 빌드 로직을 수행
    try:
        # 빌드 작업
        print(f'Build: {imageName}:{imageTag}')

        # 1분 후에 빌드 완료
        time.sleep(20)

        # 빌드 성공 시에는 이미지 이름과 태그를 저장
        project = Project.query.filter_by(id=projectId).first()
        createBuildAndSave(project.id, commitMsg, imageName, imageTag)

        # 프로젝트 상태를 빌드 완료로 변경
        project.status = 2
        db.session.commit()

    except Exception as e:
        # 빌드 실패 시에는 프로젝트 상태를 빌드 실패로 변경
        project.status = 5
        db.session.commit()

    return