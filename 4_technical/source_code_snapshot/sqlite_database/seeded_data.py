import sqlite3
import random
from faker import Faker
from datetime import timedelta

fake = Faker()
random.seed(42)
Faker.seed(42)

# change this to local file path 
DB_PATH = "mydb.sqlite"   

NUM_USERS = 500
NUM_GROUPS = 40
NUM_CHALLENGES = 80
NUM_ACTION_LOGS = 600
NUM_MOD_REQUESTS = 60

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
    
# Uncomoment the following line if you want to clear existing data before seeding new data
clear_tables()

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
    ("walk", "travel", "KM", 0.7),
    ("bus", "travel", "KM", 0.9),
    ("bike", "travel", "KM", 0.8),
    ("train", "travel", "KM", 0.5),
    ("car", "travel", "KM", 0.4),
    ("Alternative Meat", "food", "KG", 3.030),
    ("Apples", "food", "KG", 0.513),
    ("Apricots", "food", "KG", 0.811),
    ("Artichoke Plants", "food", "KG", 0.988),
    ("Artichokes", "food", "KG", 0.988),
    ("Asparagus", "food", "KG", 1.347),
    ("Aubergines", "food", "KG", 0.960),
    ("Baking/Cooking Supplies", "food", "KG", 1.534),
    ("Beef", "food", "KG", 70.164),
    ("Beer", "food", "KG", 0.690),
    ("Beetroot", "food", "KG", 0.319),
    ("Biscuits/Cookies", "food", "KG", 3.238),
    ("Bison/Buffalo", "food", "KG", 113.291),
    ("Black Eyed Peas", "food", "KG", 1.145),
    ("Blackberries", "food", "KG", 1.060),
    ("Blueberries", "food", "KG", 1.197),
    ("Bread", "food", "KG", 1.483),
    ("Breakfast Cereal", "food", "KG", 2.773),
    ("Broccoli", "food", "KG", 0.674),
    ("Brussel Sprouts", "food", "KG", 0.387),
    ("Butter", "food", "KG", 3.259),
    ("Carrots", "food", "KG", 0.294),
    ("Cassava", "food", "KG", 0.726),
    ("Cauliflower", "food", "KG", 0.674),
    ("Celery", "food", "KG", 0.401),
    ("Cheese", "food", "KG", 4.114),
    ("Chicken", "food", "KG", 3.927),
    ("Chicken (Processed)", "food", "KG", 5.760),
    ("Chickpeas", "food", "KG", 1.014),
    ("Chocolate/Confectionery", "food", "KG", 4.996),
    ("Chutneys/Relishes", "food", "KG", 3.180),
    ("Coffee", "food", "KG", 6.976),
    ("Condiments/Sauces", "food", "KG", 1.733),
    ("Cooking Oil", "food", "KG", 2.867),
    ("Cooking Sauces (Fresh)", "food", "KG", 1.616),
    ("Cooking Sauces (Shelf Stable)", "food", "KG", 1.616),
    ("Courgettes", "food", "KG", 0.863),
    ("Cranberries", "food", "KG", 0.768),
    ("Cream", "food", "KG", 1.665),
    ("Cucumbers", "food", "KG", 0.405),
    ("Dates", "food", "KG", 2.713),
    ("Dessert Sauces/Toppings", "food", "KG", 1.782),
    ("Dressings/Dips", "food", "KG", 3.429),
    ("Egg Products", "food", "KG", 1.659),
    ("Eggs", "food", "KG", 1.228),
    ("Fennel", "food", "KG", 0.144),
    ("Figs", "food", "KG", 0.459),
    ("Fish", "food", "KG", 2.616),
    ("Fish (Processed)", "food", "KG", 2.807),
    ("Flavoured Drinks", "food", "KG", 0.533),
    ("Fruit Juice", "food", "KG", 1.541),
    ("Garlic", "food", "KG", 1.197),
    ("Ginger", "food", "KG", 1.245),
    ("Gooseberries", "food", "KG", 0.513),
    ("Grains/Flour", "food", "KG", 1.534),
    ("Grapes", "food", "KG", 0.871),
    ("Ice Cream", "food", "KG", 2.554),
    ("Kiwifruits", "food", "KG", 0.717),
    ("Lamb", "food", "KG", 38.144),
    ("Lemons", "food", "KG", 0.641),
    ("Lentils", "food", "KG", 3.433),
    ("Limes", "food", "KG", 0.616),
    ("Mandarins", "food", "KG", 0.602),
    ("Margarine", "food", "KG", 3.220),
    ("Meat Substitutes", "food", "KG", 0.710),
    ("Milk", "food", "KG", 0.341),
    ("Mushrooms", "food", "KG", 0.288),
    ("Nuts/Seeds", "food", "KG", 3.017),
    ("Olives", "food", "KG", 1.966),
    ("Onions", "food", "KG", 0.647),
    ("Oranges", "food", "KG", 0.618),
    ("Pears", "food", "KG", 0.459),
    ("Peas", "food", "KG", 1.018),
    ("Pineapples", "food", "KG", 0.563),
    ("Plant-Based Milk", "food", "KG", 0.455),
    ("Pork", "food", "KG", 4.762),
    ("Pork (Processed)", "food", "KG", 4.356),
    ("Potatoes", "food", "KG", 0.462),
    ("Pumpkin/Squash", "food", "KG", 0.863),
    ("Quinces", "food", "KG", 0.459),
    ("Raspberries", "food", "KG", 0.745),
    ("Sparkling Wine", "food", "KG", 1.615),
    ("Strawberries", "food", "KG", 0.418),
    ("Swede/Rutabaga", "food", "KG", 0.294),
    ("Sweetcorn", "food", "KG", 0.597),
    ("Tomato Ketchup", "food", "KG", 1.847),
    ("Tomatoes", "food", "KG", 0.456),
    ("Turkey", "food", "KG", 5.675),
    ("Vegetables (Processed)", "food", "KG", 0.889),
    ("Watermelons", "food", "KG", 0.395),
    ("Wine", "food", "KG", 1.615),
    ("Yogurt", "food", "KG", 0.511),
    ("Yogurt Substitutes", "food", "KG", 0.585),
    ("cold-wash", "energy", "Load", 0.176),
    ("air-dry", "energy", "Load", 0.725),
    ("heating", "energy", "HR", 0.148),
    ("lights", "energy", "HR", 0.01056),
    ("recycle-paper", "waste", "KG", 1.0),
    ("recycle-cardboard", "waste", "KG", 1.0),
    ("recycle-plastic", "waste", "KG", 1.2),
    ("recycle-glass", "waste", "KG", 0.3),
    ("recycle-aluminium", "waste", "KG", 9.5),
    ("recycle-steel", "waste", "KG", 1.5),
    ("compost-food", "waste", "KG", 0.5),
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
    challenge_type = random.choice(["Personal", "Group"])
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
    if challenge_meta[challenge_id]["challenge_type"] != "Personal":
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
    if challenge_meta[challenge_id]["challenge_type"] != "Group":
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

    if ctype == "Personal":
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