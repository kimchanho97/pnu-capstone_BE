class AuthorizationError(Exception):
    pass

class ProjectNotFoundError(Exception):
    pass

class CreatingProjectHelmError(Exception):
    pass

class BuildExistsError(Exception):
    pass

class ArgoWorkflowError(Exception):
    pass

class BuildNotFoundError(Exception):
    pass

class DeployExistsError(Exception):
    pass

class DeployingProjectHelmError(Exception):
    pass