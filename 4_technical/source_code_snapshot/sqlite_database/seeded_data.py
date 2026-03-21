import sqlite3
import random
from faker import Faker
from datetime import timedelta

fake = Faker()
random.seed(42)
Faker.seed(42)

# change this to local file path 
DB_PATH = "C:\\Users\\Kkyua\\Desktop\\UoE\\Year 2\\Sem 2\\Team Project\\DeepCurrent-Project\\4_technical\\source_code_snapshot\\sqlite_database\\mydb.sqlite"   

NUM_USERS = 120
NUM_GROUPS = 20
NUM_CHALLENGES = 40
NUM_ACTION_LOGS = 220
NUM_MOD_REQUESTS = 25

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

def ts_between(start_days_ago=365, end_days_ago=0):
    dt = fake.date_time_between(
        start_date=f"-{start_days_ago}d",
        end_date=f"-{end_days_ago}d"
    )
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def safe_choice(items):
    return random.choice(items) if items else None

def weighted_bool(true_weight=0.25):
    return 1 if random.random() < true_weight else 0

# Optional: wipe existing data before seeding
def clear_tables():
    tables = [
        "Decision",
        "Evidence",
        "ChallengeAction",
        "GroupParticipation",
        "IndividualParticipation",
        "Challenge",
        "ActionLog",
        "ActionType",
        "AccountGroup",
        "UserGroup",
        "ModRequest",
        "Accounts",
        "Users"
    ]
    cursor.execute("PRAGMA foreign_keys = OFF;")
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table};")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
        except sqlite3.OperationalError:
            pass
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()

# 1. Users
user_ids = []
for _ in range(NUM_USERS):
    user_type = random.choice(["student", "staff"])
    course = fake.word().title() if user_type == "student" else None
    department = fake.word().title() if user_type == "staff" else None

    cursor.execute("""
        INSERT INTO Users (
            first_name, last_name, dob, email, user_type, course, department
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        fake.first_name(),
        fake.last_name(),
        fake.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        fake.unique.email(),
        user_type,
        course,
        department
    ))
    user_ids.append(cursor.lastrowid)

# 2. Accounts
account_ids = []
moderator_ids = []

for user_id in user_ids:
    is_moderator = weighted_bool(0.15)

    cursor.execute("""
        INSERT INTO Accounts (
            user_id, username, password, is_moderator, date_created, last_active
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        fake.unique.user_name(),
        "hashed_password",
        is_moderator,
        ts_between(365, 60),
        ts_between(30, 0)
    ))
    account_id = cursor.lastrowid
    account_ids.append(account_id)
    if is_moderator:
        moderator_ids.append(account_id)

# Ensure at least a few moderators exist
if len(moderator_ids) < 5:
    needed = 5 - len(moderator_ids)
    extras = random.sample(account_ids, needed)
    for acc_id in extras:
        cursor.execute("""
            UPDATE Accounts
            SET is_moderator = 1
            WHERE account_id = ?
        """, (acc_id,))
        moderator_ids.append(acc_id)

# 3. ModRequest
for _ in range(NUM_MOD_REQUESTS):
    requester = safe_choice(account_ids)
    reviewer = safe_choice(moderator_ids) or safe_choice(account_ids)
    request_status = random.choice(["pending", "approved", "rejected"])

    cursor.execute("""
        INSERT INTO ModRequest (
            account_id, reviewed_by, submitted_at, request_status
        )
        VALUES (?, ?, ?, ?)
    """, (
        requester,
        reviewer,
        ts_between(180, 0),
        request_status
    ))

# 4. UserGroup
group_ids = []
group_leaders = {}

for _ in range(NUM_GROUPS):
    creator = safe_choice(account_ids)

    cursor.execute("""
        INSERT INTO UserGroup (
            group_creator_id, group_name, group_created
        )
        VALUES (?, ?, ?)
    """, (
        creator,
        fake.unique.company(),
        ts_between(300, 30)
    ))
    group_id = cursor.lastrowid
    group_ids.append(group_id)
    group_leaders[group_id] = creator

# 5. AccountGroup
account_group_pairs = set()

for group_id in group_ids:
    leader = group_leaders[group_id]

    cursor.execute("""
        INSERT INTO AccountGroup (
            account_id, group_id, roles, joined
        )
        VALUES (?, ?, ?, ?)
    """, (
        leader,
        group_id,
        "leader",
        ts_between(250, 20)
    ))
    account_group_pairs.add((leader, group_id))

    member_count = random.randint(4, 10)
    possible_members = [a for a in account_ids if a != leader]
    sampled_members = random.sample(possible_members, min(member_count, len(possible_members)))

    for account_id in sampled_members:
        if (account_id, group_id) in account_group_pairs:
            continue
        cursor.execute("""
            INSERT INTO AccountGroup (
                account_id, group_id, roles, joined
            )
            VALUES (?, ?, ?, ?)
        """, (
            account_id,
            group_id,
            "member",
            ts_between(250, 10)
        ))
        account_group_pairs.add((account_id, group_id))

# Reverse lookup: account -> groups
account_to_groups = {}
for account_id, group_id in account_group_pairs:
    account_to_groups.setdefault(account_id, []).append(group_id)

# 6. ActionType
action_type_ids = []
action_type_meta = {}

action_types = [
    ("Bus Travel", "transport", "km", 0.12),
    ("Cycling", "transport", "km", 0.00),
    ("Electricity Usage", "energy", "kWh", 0.18),
    ("Solar Usage", "energy", "kWh", 0.03),
    ("Recycling", "waste", "kg", 0.05),
    ("Composting", "waste", "kg", 0.04),
    ("Plant-based Meal", "food", "meal", 0.10),
    ("Low-carbon Meal", "food", "meal", 0.15),
]

for actionName, category, unit, co2e_factor in action_types:
    cursor.execute("""
        INSERT INTO ActionType (
            actionName, category, unit, co2e_factor
        )
        VALUES (?, ?, ?, ?)
    """, (actionName, category, unit, co2e_factor))
    action_type_id = cursor.lastrowid
    action_type_ids.append(action_type_id)
    action_type_meta[action_type_id] = {
        "actionName": actionName,
        "category": category,
        "unit": unit,
        "co2e_factor": co2e_factor
    }

# 7. Challenge
challenge_ids = []
challenge_meta = {}

for _ in range(NUM_CHALLENGES):
    created_by = safe_choice(account_ids)
    challenge_type = random.choice(["individual", "group"])
    title = fake.sentence(nb_words=4)[:50]
    start_dt = fake.date_time_between(start_date="-120d", end_date="-20d")
    end_dt = start_dt + timedelta(days=random.randint(7, 30))
    rules = fake.text(max_nb_chars=120)

    cursor.execute("""
        INSERT INTO Challenge (
            created_by, challenge_type, title, start_date, end_date, rules
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        created_by,
        challenge_type,
        title,
        start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        rules
    ))

    challenge_id = cursor.lastrowid
    challenge_ids.append(challenge_id)
    challenge_meta[challenge_id] = {
        "challenge_type": challenge_type,
        "start_date": start_dt,
        "end_date": end_dt
    }

# 8. IndividualParticipation
individual_pairs = set()
for challenge_id in challenge_ids:
    if challenge_meta[challenge_id]["challenge_type"] != "individual":
        continue

    participants = random.sample(account_ids, random.randint(5, min(20, len(account_ids))))
    for account_id in participants:
        if (challenge_id, account_id) in individual_pairs:
            continue
        cursor.execute("""
            INSERT INTO IndividualParticipation (
                challenge_id, account_id, joined_date
            )
            VALUES (?, ?, ?)
        """, (
            challenge_id,
            account_id,
            ts_between(90, 0)
        ))
        individual_pairs.add((challenge_id, account_id))

# 9. GroupParticipation
group_pairs = set()
for challenge_id in challenge_ids:
    if challenge_meta[challenge_id]["challenge_type"] != "group":
        continue

    participants = random.sample(group_ids, random.randint(3, min(8, len(group_ids))))
    for group_id in participants:
        if (challenge_id, group_id) in group_pairs:
            continue
        cursor.execute("""
            INSERT INTO GroupParticipation (
                challenge_id, group_id, joined_date
            )
            VALUES (?, ?, ?)
        """, (
            challenge_id,
            group_id,
            ts_between(90, 0)
        ))
        group_pairs.add((challenge_id, group_id))

# Helpers
challenge_to_individual_accounts = {}
for challenge_id, account_id in individual_pairs:
    challenge_to_individual_accounts.setdefault(challenge_id, []).append(account_id)

challenge_to_groups = {}
for challenge_id, group_id in group_pairs:
    challenge_to_groups.setdefault(challenge_id, []).append(group_id)

# 10. ActionLog
log_ids = []
log_owner = {}

for _ in range(NUM_ACTION_LOGS):
    submitted_by = safe_choice(account_ids)
    actionType_id = safe_choice(action_type_ids)
    quantity = random.randint(1, 10)
    log_date = fake.date_time_between(start_date="-100d", end_date="now")

    co2e_saved = round(quantity * action_type_meta[actionType_id]["co2e_factor"], 3)

    cursor.execute("""
        INSERT INTO ActionLog (
            submitted_by, actionType_id, log_date, quantity, co2e_saved
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        submitted_by,
        actionType_id,
        log_date.strftime("%Y-%m-%d %H:%M:%S"),
        quantity,
        co2e_saved
    ))
    log_id = cursor.lastrowid
    log_ids.append(log_id)
    log_owner[log_id] = submitted_by

# 11. ChallengeAction
challenge_action_ids = []
used_pairs = set()

for challenge_id in challenge_ids:
    ctype = challenge_meta[challenge_id]["challenge_type"]

    if ctype == "individual":
        valid_accounts = challenge_to_individual_accounts.get(challenge_id, [])
        valid_logs = [lid for lid in log_ids if log_owner[lid] in valid_accounts]
        selected_logs = random.sample(valid_logs, min(len(valid_logs), random.randint(5, 15)))

        for log_id in selected_logs:
            if (challenge_id, log_id) in used_pairs:
                continue
            used_pairs.add((challenge_id, log_id))

            point_awarded = random.randint(5, 40)

            cursor.execute("""
                INSERT INTO ChallengeAction (
                    challenge_id, group_id, log_id, point_awarded
                )
                VALUES (?, ?, ?, ?)
            """, (
                challenge_id,
                None,
                log_id,
                point_awarded
            ))
            challenge_action_ids.append(cursor.lastrowid)

    else:
        valid_groups = challenge_to_groups.get(challenge_id, [])
        for group_id in valid_groups:
            member_accounts = [acc for acc, grp in account_group_pairs if grp == group_id]
            valid_logs = [lid for lid in log_ids if log_owner[lid] in member_accounts]
            selected_logs = random.sample(valid_logs, min(len(valid_logs), random.randint(2, 8)))

            for log_id in selected_logs:
                if (challenge_id, log_id) in used_pairs:
                    continue
                used_pairs.add((challenge_id, log_id))

                point_awarded = random.randint(5, 40)

                cursor.execute("""
                    INSERT INTO ChallengeAction (
                        challenge_id, group_id, log_id, point_awarded
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    challenge_id,
                    group_id,
                    log_id,
                    point_awarded
                ))
                challenge_action_ids.append(cursor.lastrowid)

# 12. Evidence
evidence_ids = []
challenge_action_to_log = {}

cursor.execute("SELECT challengeAction_id, log_id FROM ChallengeAction")
for ca_id, log_id in cursor.fetchall():
    challenge_action_to_log[ca_id] = log_id

sampled_ca = random.sample(challenge_action_ids, min(100, len(challenge_action_ids)))
for ca_id in sampled_ca:
    log_id = challenge_action_to_log[ca_id]
    num_items = random.randint(1, 2)

    for _ in range(num_items):
        cursor.execute("""
            INSERT INTO Evidence (
                log_id, evidence_type, evidence_url, evidence_date
            )
            VALUES (?, ?, ?, ?)
        """, (
            log_id,
            random.choice(["photo", "receipt", "screenshot"]),
            fake.url(),
            ts_between(60, 0)
        ))
        evidence_ids.append(cursor.lastrowid)

# 13. Decision
for evidence_id in random.sample(evidence_ids, min(70, len(evidence_ids))):
    reviewer_id = safe_choice(moderator_ids) or safe_choice(account_ids)
    decision_status = random.choice(["approved", "rejected"])
    decision_date = ts_between(45, 0)

    cursor.execute("""
        INSERT INTO Decision (
            evidence_id, reviewer_id, decision_status, decision_date, reason
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        evidence_id,
        reviewer_id,
        decision_status,
        decision_date,
        fake.sentence(nb_words=8)
    ))

conn.commit()

# Summary
for table in [
    "Users", "Accounts", "ModRequest", "UserGroup", "AccountGroup",
    "ActionType", "ActionLog", "Challenge", "IndividualParticipation",
    "GroupParticipation", "ChallengeAction", "Evidence", "Decision"
]:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"{table}: {cursor.fetchone()[0]}")

cursor.close()
conn.close()
print("Seeding complete.")