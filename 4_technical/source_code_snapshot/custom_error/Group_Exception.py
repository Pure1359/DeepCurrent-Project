class UserAlreadyJoinGroup(Exception):
    def __init__(self, message):
        super().__init__(message)

class DuplicateGroupName(Exception):
    def __init__(self, message):
        super().__init__(message)
class LeaveGroupError(Exception):
    def __init__(self, message):
        super().__init__(message)
class GroupPermissionError(Exception):
    def __init__(self, message):
        super().__init__(message)