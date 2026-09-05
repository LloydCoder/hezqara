from app.workforce.base.policy import PermissionPolicy

class RevenueCyclePolicy(PermissionPolicy):
    def __init__(self): super().__init__('claims:read')
