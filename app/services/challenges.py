from app.db_config import close_connection, db_cursor, get_connection
# Placeholder for now
# Create functions that have to do with challenges
# Follow templates in users.py and auth.py
# Some Ideas:
# create_challenge
# join_challenge_individual
# join_challenge_group
# challenge_leaderboard_individual
# challenge_leaderboard_group
    

#Required role : Who can create the challenge? Parameter : Role -> {Admin, Locally Group Leader , etc}
def create_challenge():
    get_connection(challengeType, challengeTitle, challengeStartDate, challengeEndDate, challengeRules):
    sql = "INSERT INTO Challenge challengeType AND challengeTitle AND challengeStartDate AND challengeEndDate AND challengeRules VALUES (%s)"

    close_connection()

def join_challenge_individual():
    pass

def join_challenge_group():
    pass

def challenge_leaderboard_individual():
    pass

def challenge_leaderboard_group():
    pass

