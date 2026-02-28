class InvalidChallengeDate(Exception):
    def __init__(self, message):
        super().__init__(message)

class ChallengeIdNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)

class UserAlreadyJoinChallenge(Exception):
    def __init__(self, message):
        super().__init__(message)
class GroupAlreadyJoinChallenge(Exception):
    def __init__(self, message):
        super().__init__(message)

