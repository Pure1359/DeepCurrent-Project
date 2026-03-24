from app.db_config import db_cursor
from flask import Response, jsonify, session, abort
from datetime import datetime, timedelta
from pymysql.cursors import DictCursor
from app.services.badges import check_and_award_badges
import hashlib

# Define limits for anti-gaming checks
# Min = minimum quantity for action
# Max = High quantity for action (Raise medium flag)
# Hard_max = maximum quantity for action (Raise high flag)
# Daily_limit = maximum number of actions per day
ACTION_LIMITS = {
    ("walk", "travel"): {"min": 0.2, "max": 20, "hard_max": 60, "daily_limit": 4},
    ("bus", "travel"): {"min": 0.5, "max": 80, "hard_max": 200, "daily_limit": 6},
    ("bike", "travel"): {"min": 0.5, "max": 40, "hard_max": 120, "daily_limit": 4},
    ("train", "travel"): {"min": 1, "max": 150, "hard_max": 400, "daily_limit": 4},
    ("car", "travel"): {"min": 0.5, "max": 100, "hard_max": 250, "daily_limit": 4},

    ("heating", "energy"): {"min": 0.5, "max": 12, "hard_max": 24, "daily_limit": 4},
    ("lights", "energy"): {"min": 0.5, "max": 12, "hard_max": 24, "daily_limit": 6},
    ("cold-wash", "energy"): {"min": 1, "max": 3, "hard_max": 8, "daily_limit": 3},
    ("air-dry", "energy"): {"min": 1, "max": 3, "hard_max": 8, "daily_limit": 3},

    ("recycle-paper", "waste"): {"min": 0.1, "max": 10, "hard_max": 25, "daily_limit": 4},
    ("recycle-cardboard", "waste"): {"min": 0.1, "max": 10, "hard_max": 25, "daily_limit": 4},
    ("recycle-plastic", "waste"): {"min": 0.1, "max": 8, "hard_max": 20, "daily_limit": 4},
    ("recycle-glass", "waste"): {"min": 0.1, "max": 15, "hard_max": 30, "daily_limit": 4},
    ("recycle-aluminium", "waste"): {"min": 0.1, "max": 5, "hard_max": 15, "daily_limit": 4},
    ("recycle-steel", "waste"): {"min": 0.1, "max": 8, "hard_max": 20, "daily_limit": 4},
    ("compost-food", "waste"): {"min": 0.1, "max": 5, "hard_max": 15, "daily_limit": 3},
}

# Contradictory actions. 
# For example, you cannot drive to campus and walk to campus at the same time
CONTRADICTORY_ACTIONS = {
    ("walk", "travel"): [("car", "travel"), ("bus", "travel"), ("train", "travel")],
    ("bike", "travel"): [("car", "travel"), ("bus", "travel"), ("train", "travel")],
    ("car", "travel"): [("walk", "travel"), ("bike", "travel")],
    ("bus", "travel"): [("walk", "travel"), ("bike", "travel")],
    ("train", "travel"): [("walk", "travel"), ("bike", "travel")],
}

# Anti-Gaming Checks helper functions
def _normalize_key(name, category):
    return (str(name).strip().lower(), str(category).strip().lower())

def _hash_evidence_value(evidence_url):
    if not evidence_url:
        return None
    return hashlib.sha256(str(evidence_url).strip().encode("utf-8")).hexdigest()

def create_antigaming_flags(cursor: DictCursor, action_log_id, account_id, flags):
    sql = """
        INSERT INTO AntiGamingFlag(action_log_id, account_id, rule_code, severity, status, reason, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    now = datetime.now()
    for flag in flags:
        cursor.execute(sql, (
            action_log_id,
            account_id,
            flag["rule_code"],
            flag["severity"],
            "open",
            flag["reason"],
            now
        ))

def get_antigaming_flags_for_action(action_log_id):
    sql = """
        SELECT flag_id, action_log_id, account_id, rule_code, severity, status, reason, created_at, reviewed_by, reviewed_at
        FROM AntiGamingFlag
        WHERE action_log_id = %s
        ORDER BY created_at DESC
    """
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (action_log_id,))
        return cursor.fetchall()

#Log action into database, dispatches to log_travel or log_food based on category
def log_action(account_id, name, category, quantity, challenge_id = None, evidence_url = None):
    if category == "food":
        return log_food(account_id, name, category, quantity, challenge_id, evidence_url)
    else:
        return log_simple_action(account_id, name, category, quantity, challenge_id, evidence_url)

def log_simple_action(account_id, name, category, quantity, challenge_id = None, evidence_url = None):
    current_time = datetime.now()
    co2e_saved = 0

    sqlActionType = """SELECT * FROM ActionType
                       WHERE actionName = %s AND category = %s
                    """

    sqlActionLog = """INSERT INTO ActionLog(submitted_by, actionType_id, log_date, quantity, co2e_saved) VALUES (%s, %s, %s, %s, %s)"""

    with db_cursor() as (connection, cursor):
        cursor.execute(sqlActionType, (name, category))
        return_record = cursor.fetchone()
        if return_record is None:
            raise ValueError(f"Action type does not exists: {name}, {category}")

        actionType_id = return_record["actionType_id"]
        co2e_factor = return_record["co2e_factor"]
        co2e_saved = co2e_factor * quantity

        cursor.execute(sqlActionLog, (account_id, actionType_id, current_time, quantity, co2e_saved))

        action_log_id = cursor.lastrowid

        inserted_decision_id = None
        inserted_evidence_id = None
        challenge_action_id = None

        flags, evidence_hash = run_antigaming_checks(
            cursor=cursor,
            account_id=account_id,
            action_type_id=actionType_id,
            action_name=name,
            category=category,
            quantity=quantity,
            log_date=current_time,
            evidence_url=evidence_url,
            challenge_id=challenge_id
        )

        if evidence_url is not None:
            inserted_evidence_id = insert_evidence_record(
                cursor,
                action_log_id,
                None,
                evidence_url,
                current_time,
                evidence_hash
            )

            inserted_decision_id = insert_decision_record(
                cursor,
                inserted_evidence_id,
                None,
                "pending" if flags else "approved",
                None if flags else current_time,
                "Auto-flagged for moderator review." if flags else "Auto-approved at submission."
            )

        if flags:
            create_antigaming_flags(cursor, action_log_id, account_id, flags)

        # Only award challenge points immediately if not flagged
        if challenge_id is not None:
            if evidence_url is None:
                raise ValueError("Can not submit to challenge with no evidence")
            if not flags:
                challenge_action_id = apply_to_challenge(cursor, challenge_id, action_log_id, co2e_saved, account_id)
                check_and_award_badges(account_id)

        return {
            "action_log_id" : action_log_id,
            "evidence_id" : inserted_evidence_id,
            "decision_id" : inserted_decision_id,
            "challenge_id" : challenge_id,
            "challenge_action_id" : challenge_action_id,
            "co2e_factor" : co2e_factor,
            "co2e_saved" : co2e_saved,
            "flags" : flags
        }

def log_food(account_id, name, category, quantity, challenge_id = None, evidence_url = None):
    if len(quantity) > 5:
        raise ValueError("A meal can contain at most 5 ingredients")
    current_time = datetime.now()
    food_text = ""
    co2e_saved = 0
    last_actionType_id = None
    sqlActionType = """SELECT * FROM ActionType
                       WHERE actionName = %s AND category = 'food'
                    """
    sqlActionLog = """INSERT INTO ActionLog(submitted_by, actionType_id, log_date, quantity, co2e_saved) VALUES (%s, %s, %s, %s, %s)"""

    with db_cursor() as (connection, cursor):
        # quantity is a list of (ingredient_name, kg) tuples
        for food_name, kg in quantity:
            food_text += f"{food_name}:{kg} "
            cursor.execute(sqlActionType, (food_name,))
            return_record = cursor.fetchone()
            if return_record is None:
                raise ValueError(f"Action type does not exists: {food_name}, {category}")
            last_actionType_id = return_record["actionType_id"]
            co2e_factor = return_record["co2e_factor"]
            co2e_saved = co2e_saved + (co2e_factor * kg)
        cursor.execute(sqlActionLog, (account_id, last_actionType_id, current_time, food_text.strip(), co2e_saved))
        action_log_id = cursor.lastrowid
        inserted_decision_id = None
        inserted_evidence_id = None
        challenge_action_id = None

        evidence_hash = _hash_evidence_value(evidence_url)

        if challenge_id is not None and evidence_url is None:
            raise ValueError("Can not submit to challenge with no evidence")

        if evidence_url is not None:
            inserted_evidence_id = insert_evidence_record(
                cursor,
                action_log_id,
                None,
                evidence_url,
                current_time,
                evidence_hash
            )
            inserted_decision_id = insert_decision_record(cursor, inserted_evidence_id, None, "pending", None, None)

        if challenge_id is not None:
            challenge_action_id = apply_to_challenge(cursor, challenge_id, action_log_id, co2e_saved, account_id)
            check_and_award_badges(account_id)

        return {
            "action_log_id": action_log_id,
            "evidence_id": inserted_evidence_id,
            "decision_id": inserted_decision_id,
            "challenge_id": challenge_id,
            "challenge_action_id": challenge_action_id,
            "co2e_saved": co2e_saved
        }
    # quantity is a list of (ingredient_name, kg) tuples   

def insert_evidence_record(cursor:DictCursor, action_log_id, evidence_type, evidence_url, evidence_date, file_hash=None):
    insert_evidence = """INSERT INTO Evidence(log_id, evidence_type, evidence_url, evidence_date, file_hash) VALUES (%s, %s, %s, %s, %s)"""
    cursor.execute(insert_evidence, (action_log_id, evidence_type, evidence_url, evidence_date, file_hash))
    return cursor.lastrowid

def insert_decision_record(cursor:DictCursor, evidence_id, reviewer_id, decision_status, decision_date, reason):
    insert_decision = """INSERT INTO Decision(evidence_id, reviewer_id, decision_status, decision_date, reason) VALUES(%s, %s, %s, %s, %s)"""
    cursor.execute(insert_decision, (evidence_id, reviewer_id, decision_status, decision_date, reason))
    return cursor.lastrowid


#Find the challenge that is eligible to be applied to
def apply_to_challenge(cursor:DictCursor, challenge_id, action_log_id, co2e_saved, account_id):

    #Find out the challenge type (Personal or Group)
    check_type = """SELECT challenge_type FROM Challenge WHERE challenge_id = %s"""
    cursor.execute(check_type, (challenge_id,))
    challenge = cursor.fetchone()
    if challenge is None:
        raise ValueError(f"Challenge {challenge_id} does not exist")

    group_id = None

    if challenge["challenge_type"] == "Group":
        #For group challenges, check if users group has joined this challenge
        check_group_joined = """SELECT gp.group_id FROM GroupParticipation gp
                                JOIN AccountGroup ag ON ag.group_id = gp.group_id
                                WHERE gp.challenge_id = %s AND ag.account_id = %s"""
        cursor.execute(check_group_joined, (challenge_id, account_id))
        group_result = cursor.fetchone()
        if group_result is None:
            raise ValueError(f"Your group has not joined challenge {challenge_id}")
        group_id = group_result["group_id"]
    else:
        #For personal challenges, check if user has joined individually
        check_joined = """SELECT challenge_id FROM IndividualParticipation WHERE challenge_id = %s AND account_id = %s"""
        cursor.execute(check_joined, (challenge_id, account_id))
        if cursor.fetchone() is None:
            raise ValueError(f"You have not joined challenge {challenge_id}")

    insertion = """INSERT INTO ChallengeAction(challenge_id, group_id, log_id, point_awarded) VALUES (%s, %s, %s, %s)"""
    points_awarded = co2e_saved
    cursor.execute(insertion, (challenge_id, group_id, action_log_id, points_awarded))
    return cursor.lastrowid

def get_action_history(account_id, limit, offset):
    sql = """SELECT 
                actionName,
                category,
                challenge_id,
                co2e_factor,
                quantity,
                evidence_url,
                evidence_type,
                evidence_date,
                decision_status,
                unit
            FROM ActionLog
            LEFT JOIN Evidence 
                ON ActionLog.log_id = Evidence.log_id
            LEFT JOIN Decision 
                ON Evidence.evidence_id = Decision.evidence_id
            LEFT JOIN ActionType 
                ON ActionType.actionType_id = ActionLog.actionType_id
            LEFT JOIN ChallengeAction
                ON ChallengeAction.log_id = ActionLog.log_id
            WHERE submitted_by = %s
            ORDER BY evidence_date DESC
            LIMIT %s OFFSET %s
         """
     
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (account_id, limit, offset))
        action_list = cursor.fetchall()
        return jsonify(action_list)
    
def personal_dashboard(account_id):
    totals_sql = """
        SELECT
            COALESCE(SUM(ca.point_awarded), 0) AS total_points,
            COALESCE(SUM(al.co2e_saved), 0) AS total_co2e_saved,
            COUNT(al.log_id) AS actions_count
        FROM ActionLog al
        LEFT JOIN ChallengeAction ca ON ca.log_id = al.log_id
        WHERE al.submitted_by = %s
    """
    recent_sql = """
        SELECT al.log_id, at.actionName, at.category, al.quantity, at.unit, al.co2e_saved, al.log_date
        FROM ActionLog al
        JOIN ActionType at ON at.actionType_id = al.actionType_id
        WHERE al.submitted_by = %s
        ORDER BY al.log_date DESC
        LIMIT 10
    """
    with db_cursor() as (connection, cursor):
        cursor.execute(totals_sql, (account_id,))
        totals = cursor.fetchone() or {"total_points": 0, "total_co2e_saved": 0, "actions_count": 0}
        cursor.execute(recent_sql, (account_id,))
        recent = cursor.fetchall()
    return {"totals": totals, "recent_actions": recent}

def leaderboard(limit):
    sql = """
        SELECT
            a.account_id,
            u.first_name,
            u.last_name,
            COALESCE(SUM(ca.point_awarded), 0) AS points
        FROM Accounts a
        JOIN Users u ON u.user_id = a.user_id
        LEFT JOIN ActionLog al ON al.submitted_by = a.account_id
        LEFT JOIN ChallengeAction ca ON ca.log_id = al.log_id
        GROUP BY a.account_id, u.first_name, u.last_name
        ORDER BY points DESC
        LIMIT %s
    """
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (limit,))
        return cursor.fetchall()

def run_antigaming_checks(cursor: DictCursor, account_id, action_type_id, action_name, category, quantity, log_date, evidence_url=None, challenge_id=None):
    flags = []
    action_key = _normalize_key(action_name, category)
    limits = ACTION_LIMITS.get(action_key)
    evidence_hash = _hash_evidence_value(evidence_url)

    # Duplicate submission
    duplicate_sql = """
        SELECT COUNT(*) AS cnt
        FROM ActionLog
        WHERE submitted_by = %s
          AND actionType_id = %s
          AND quantity = %s
          AND log_date >= %s
          AND log_date < %s
    """
    duplicate_window_start = log_date - timedelta(minutes=2)
    cursor.execute(duplicate_sql, (account_id, action_type_id, str(quantity), duplicate_window_start, log_date))
    duplicate_count = (cursor.fetchone() or {}).get("cnt", 0)
    if duplicate_count > 0:
        flags.append({
            "rule_code": "duplicate_submission",
            "severity": "high",
            "reason": "Same action type and quantity was already submitted within the last 2 minutes."
        })

    # Unrealistic frequency
    if limits and limits.get("daily_limit") is not None:
        freq_sql = """
            SELECT COUNT(*) AS cnt
            FROM ActionLog
            WHERE submitted_by = %s
              AND actionType_id = %s
              AND DATE(log_date) = DATE(%s)
        """
        cursor.execute(freq_sql, (account_id, action_type_id, log_date))
        day_count = (cursor.fetchone() or {}).get("cnt", 0)
        if day_count > limits["daily_limit"]:
            flags.append({
                "rule_code": "unrealistic_frequency",
                "severity": "medium",
                "reason": f"Action logged {day_count} times on the same day; expected daily limit is {limits['daily_limit']}."
            })

    # Quantity checks
    if limits:
        if quantity > limits["hard_max"]:
            flags.append({
                "rule_code": "impossible_quantity",
                "severity": "high",
                "reason": f"Quantity {quantity} exceeds hard maximum of {limits['hard_max']}."
            })
        elif quantity > limits["max"] or quantity < limits["min"]:
            flags.append({
                "rule_code": "suspicious_quantity",
                "severity": "medium",
                "reason": f"Quantity {quantity} is outside expected range {limits['min']} to {limits['max']}."
            })

    # Contradictory logs
    contradictory = CONTRADICTORY_ACTIONS.get(action_key, [])
    for other_name, other_category in contradictory:
        contradiction_sql = """
            SELECT COUNT(*) AS cnt
            FROM ActionLog al
            JOIN ActionType at ON at.actionType_id = al.actionType_id
            WHERE al.submitted_by = %s
              AND DATE(al.log_date) = DATE(%s)
              AND LOWER(at.actionName) = %s
              AND LOWER(at.category) = %s
        """
        cursor.execute(contradiction_sql, (account_id, log_date, other_name, other_category))
        contradiction_count = (cursor.fetchone() or {}).get("cnt", 0)
        if contradiction_count > 0:
            flags.append({
                "rule_code": "contradictory_log",
                "severity": "medium",
                "reason": f"Contradictory action detected on the same date: {action_name} conflicts with {other_name}."
            })
            break

    # Reused evidence
    if evidence_hash:
        reused_evidence_sql = """
            SELECT COUNT(*) AS cnt
            FROM Evidence
            WHERE file_hash = %s
        """
        cursor.execute(reused_evidence_sql, (evidence_hash,))
        evidence_count = (cursor.fetchone() or {}).get("cnt", 0)
        if evidence_count > 0:
            flags.append({
                "rule_code": "reused_evidence",
                "severity": "medium",
                "reason": "The same evidence hash has already been used in another submission."
            })

    # Challenge farming
    if challenge_id is not None:
        farming_sql_total = """
            SELECT COUNT(*) AS total_count
            FROM ChallengeAction ca
            JOIN ActionLog al ON al.log_id = ca.log_id
            WHERE ca.challenge_id = %s
              AND al.submitted_by = %s
        """
        farming_sql_same = """
            SELECT COUNT(*) AS same_count
            FROM ChallengeAction ca
            JOIN ActionLog al ON al.log_id = ca.log_id
            WHERE ca.challenge_id = %s
              AND al.submitted_by = %s
              AND al.actionType_id = %s
        """
        cursor.execute(farming_sql_total, (challenge_id, account_id))
        total_count = (cursor.fetchone() or {}).get("total_count", 0)

        cursor.execute(farming_sql_same, (challenge_id, account_id, action_type_id))
        same_count = (cursor.fetchone() or {}).get("same_count", 0)

        if total_count >= 5 and same_count / max(total_count, 1) >= 0.8:
            flags.append({
                "rule_code": "challenge_farming",
                "severity": "medium",
                "reason": "A very high proportion of challenge submissions are from the same action type."
            })

    return flags, evidence_hash

def list_antigaming_flags(limit=20, offset=0):
    sql = """
        SELECT
            f.flag_id,
            f.rule_code,
            f.severity,
            f.status,
            f.reason,
            f.created_at,
            f.action_log_id,
            f.account_id,
            at.actionName,
            at.category,
            al.quantity,
            al.log_date
        FROM AntiGamingFlag f
        JOIN ActionLog al ON al.log_id = f.action_log_id
        JOIN ActionType at ON at.actionType_id = al.actionType_id
        ORDER BY f.created_at DESC
        LIMIT %s OFFSET %s
    """
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (limit, offset))
        return cursor.fetchall()