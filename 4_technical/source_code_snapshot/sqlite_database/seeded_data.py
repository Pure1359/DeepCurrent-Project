import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta
import hashlib
from collections import defaultdict
from pathlib import Path

fake = Faker()
random.seed(42)
Faker.seed(42)

# change this to local file path 
DB_PATH = Path(__file__).resolve().parent / "mydb.sqlite"
COMMON_TEST_PASSWORD = "Password123!"
COMMON_TEST_PASSWORD_HASH = "$2b$10$9x9dbW71AfKvrNA3XwHmheNHzljROfGGG9TGuEvgEn79Il8XlVP4K"

NUM_USERS = 84
NUM_GROUPS = 12
NUM_CHALLENGES = 8
TARGET_NORMAL_ACTION_LOGS = 460
TARGET_EDGE_CASE_LOGS = 120
TARGET_EVIDENCE = 110
TARGET_DECISIONS = 70
TARGET_MOD_REQUESTS = 36
TARGET_CHALLENGE_ACTIONS = 240

BASE_NOW = datetime(2026, 3, 24, 12, 0, 0)

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

def dt(days_ago: int, hour: int = 12, minute: int = 0, second: int = 0):
    return (BASE_NOW - timedelta(days=days_ago)).replace(hour=hour, minute=minute, second=second)

def ts(days_ago: int, hour: int = 12, minute: int = 0, second: int = 0):
    return dt(days_ago, hour, minute, second).strftime("%Y-%m-%d %H:%M:%S")

def random_ts_within(days_back: int = 90):
    days_ago = random.randint(0, days_back)
    hour = random.randint(6, 22)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return ts(days_ago, hour, minute, second)

def safe_choice(items):
    return random.choice(items) if items else None

def hash_value(value: str):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

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
        "Users",
        "AntiGamingFlag",
        "AntiGamingRule",
        "UserBadge"
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

# Anti-Gaming Rules
cursor.execute(
    """
    INSERT INTO AntiGamingRule (rule_code, rule_name, severity, is_blocking, enabled) VALUES
    ('duplicate_submission', 'Duplicate submission in short time window', 'high', 1, 1),
    ('unrealistic_frequency', 'Too many repeated actions in a day', 'medium', 0, 1),
    ('contradictory_log', 'Contradictory actions logged in the same day', 'medium', 0, 1),
    ('suspicious_quantity', 'Quantity exceeds expected range', 'medium', 0, 1),
    ('impossible_quantity', 'Quantity exceeds hard maximum', 'high', 1, 1),
    ('reused_evidence', 'Evidence reused across submissions', 'medium', 0, 1),
    ('challenge_farming', 'Challenge score farming pattern detected', 'medium', 0, 1);
    """
)
conn.commit()

# Reference data
action_types = [
    ("walk", "travel", "KM", 0.137),
    ("bus", "travel", "KM", 0.106),
    ("bike", "travel", "KM", 0.137),
    ("train", "travel", "KM", 0.094),
    ("car", "travel", "KM", 0),
    ("Pepper, sweet, red, raw", "food", "KG", 1.045),
    ("Tomato, ripe, raw, origin unknown", "food", "KG", 0.456),
    ("Squash, raw", "food", "KG", 0.863),
    ("Aubergine, raw", "food", "KG", 0.960),
    ("Pumpkin, raw", "food", "KG", 0.863),
    ("Cucumber, raw", "food", "KG", 0.405),
    ("Beef, mince, 10-15% fat, raw", "food", "KG", 44.981),
    ("Beef, rump, raw", "food", "KG", 63.577),
    ("Beef, T-bone steak, raw", "food", "KG", 113.291),
    ("Bacon, frying, raw", "food", "KG", 6.535),
    ("Sausage, salami", "food", "KG", 6.020),
    ("Pork, ham, boiled, sliced", "food", "KG", 4.356),
    ("Chicken, breast, flesh and skin, raw", "food", "KG", 6.276),
    ("Chicken, leg, flesh and skin, raw", "food", "KG", 2.352),
    ("Chicken, hen, flesh and skin, raw", "food", "KG", 3.927),
    ("Coffee bean, roasted, ground", "food", "KG", 6.976),
    ("Tea, leaves", "food", "KG", 11.715),
    ("Cocoa, powder", "food", "KG", 16.907),
    ("Yogurt plain, whole milk", "food", "KG", 0.511),
    ("Cheese, firm, Danbo, 45 % fidm.", "food", "KG", 4.114),
    ("Cheese, semihard, Mozzarella, 30 % fidm.", "food", "KG", 4.114),
    ("Butter, salt added", "food", "KG", 3.259),
    ("Eggs, chicken, free-range hens (indoor), raw", "food", "KG", 1.228),
    ("Milk, whole, 3.5 % fat", "food", "KG", 0.341),
    ("Milk, partly skimmed, 1.5 % fat", "food", "KG", 0.278),
    ("Cream, whipping, 38 % fat", "food", "KG", 1.665),
    ("Salmon, atlantic, aquaculture, raw", "food", "KG", 1.990),
    ("Cod, fillet, raw", "food", "KG", 2.616),
    ("Tuna, raw", "food", "KG", 2.877),
    ("Tuna, in water, canned", "food", "KG", 2.939),
    ("Mackerel, raw", "food", "KG", 1.891),
    ("Herring, raw", "food", "KG", 2.106),
    ("Shrimps, boiled, shell removed", "food", "KG", 8.282),
    ("Trout, raw", "food", "KG", 1.483),
    ("Lamb, leg, unspecified , raw", "food", "KG", 38.144),
    ("Lamb, meat, average values, raw", "food", "KG", 38.144),
    ("Pork, loin, lean, raw", "food", "KG", 5.622),
    ("Pork, tenderloin, trimmed, raw", "food", "KG", 7.448),
    ("Pork, mince, 5-10% fat, raw", "food", "KG", 3.735),
    ("Turkey, flesh only, raw", "food", "KG", 5.675),
    ("Turkey, mince, 5-10% fat, raw", "food", "KG", 5.575),
    ("Duck, flesh only, raw", "food", "KG", 3.927),
    ("Potato, raw", "food", "KG", 0.462),
    ("Carrot, raw", "food", "KG", 0.294),
    ("Onion, raw", "food", "KG", 0.322),
    ("Garlic, raw", "food", "KG", 1.197),
    ("Ginger root, raw", "food", "KG", 1.245),
    ("Broccoli, raw", "food", "KG", 0.674),
    ("Cauliflower, all varieties, raw", "food", "KG", 0.674),
    ("Spinach, raw", "food", "KG", 0.617),
    ("Kale, raw", "food", "KG", 0.387),
    ("Cabbage, white, raw", "food", "KG", 0.387),
    ("Brussels sprouts, raw", "food", "KG", 0.387),
    ("Lettuce, iceberg (incl. crisphead types), raw", "food", "KG", 0.504),
    ("Asparagus, green, raw", "food", "KG", 1.347),
    ("Celery, raw", "food", "KG", 0.401),
    ("Leek, raw", "food", "KG", 0.601),
    ("Peas, green, raw", "food", "KG", 1.018),
    ("Beans, green, raw", "food", "KG", 0.652),
    ("Mushroom, raw", "food", "KG", 0.327),
    ("Beet, red, raw", "food", "KG", 0.319),
    ("Sweetcorn, kernels, canned", "food", "KG", 0.597),
    ("Parsley, raw", "food", "KG", 0.427),
    ("Apple, raw, all varieties", "food", "KG", 0.513),
    ("Pear, raw", "food", "KG", 0.459),
    ("Banana, raw", "food", "KG", 0.805),
    ("Orange, raw", "food", "KG", 0.618),
    ("Lemon, raw", "food", "KG", 0.641),
    ("Lime, raw", "food", "KG", 0.616),
    ("Grape, raw", "food", "KG", 0.871),
    ("Strawberry, raw", "food", "KG", 0.418),
    ("Raspberry, raw", "food", "KG", 0.745),
    ("Blueberries, raw", "food", "KG", 1.197),
    ("Watermelon, raw", "food", "KG", 0.395),
    ("Pineapple, raw", "food", "KG", 0.563),
    ("Mango, raw", "food", "KG", 0.987),
    ("Avocado, raw", "food", "KG", 1.192),
    ("Kiwi fruit, raw", "food", "KG", 0.717),
    ("Peach, raw", "food", "KG", 0.624),
    ("Apricot, raw", "food", "KG", 0.811),
    ("Cherry, raw", "food", "KG", 1.179),
    ("Plum, raw", "food", "KG", 0.501),
    ("Tangerine, raw", "food", "KG", 0.602),
    ("Rice, parboiled, raw", "food", "KG", 4.114),
    ("Pasta, raw", "food", "KG", 2.415),
    ("Oats, rolled, not enriched", "food", "KG", 1.933),
    ("Wheat, flour, wholemeal", "food", "KG", 1.534),
    ("Bread, white, roll, coarse grain", "food", "KG", 1.483),
    ("Green lentils, dried", "food", "KG", 3.433),
    ("Peas, chick/garbanzo, dry, raw", "food", "KG", 3.645),
    ("Chickpeas, canned", "food", "KG", 1.014),
    ("Kidney beans", "food", "KG", 1.145),
    ("Black beans", "food", "KG", 1.145),
    ("Beans, baked i tomato sauce, canned", "food", "KG", 1.846),
    ("Tofu, soy bean curd", "food", "KG", 1.117),
    ("Quinoa, black, raw", "food", "KG", 4.677),
    ("Honey", "food", "KG", 0.735),
    ("Sugar, sucrose, white", "food", "KG", 2.333),
    ("Chocolate, milk", "food", "KG", 4.996),
    ("Chocolate, bitter", "food", "KG", 8.160),
    ("Olive oil", "food", "KG", 5.843),
    ("Sunflower oil", "food", "KG", 2.867),
    ("Coconut milk", "food", "KG", 6.190),
    ("Peanuts, oilroasted and salted", "food", "KG", 3.436),
    ("Walnuts, dried", "food", "KG", 4.641),
    ("Almondmilk, unfortified", "food", "KG", 0.586),
    ("Oatmilk, with added calcium", "food", "KG", 0.455),
    ("Soymilk, with added calcium", "food", "KG", 0.368),
    ("Tomato ketchup, bottled", "food", "KG", 1.847),
    ("Soya sauce", "food", "KG", 1.518),
    ("Mayonnaise", "food", "KG", 3.159),
    ("Hummus, done", "food", "KG", 2.364),
    ("Peanut butter", "food", "KG", 3.826),
    ("Tomato paste, concentrated", "food", "KG", 2.563),
    ("Wine, red", "food", "KG", 1.615),
    ("Beer, lager, alc. 4.4 % by vol.", "food", "KG", 0.690),
    ("Ice cream, dairy, (wholemilk based)", "food", "KG", 2.554),
    ("Vegan burgers, soy based", "food", "KG", 0.708),
    ("Vegan sausages, soy based", "food", "KG", 0.796),
    ("Vegan minced, pea based", "food", "KG", 0.710),
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

TRAVEL_ACTIONS = ["walk", "bus", "bike", "train", "car"]
ENERGY_ACTIONS = ["cold-wash", "air-dry", "heating", "lights"]
WASTE_ACTIONS = [
    "recycle-paper",
    "recycle-cardboard",
    "recycle-plastic",
    "recycle-glass",
    "recycle-aluminium",
    "recycle-steel",
    "compost-food",
]
FOOD_ACTIONS = [
    "Apple, raw, all varieties", "Bread, white, roll, coarse grain", "Broccoli, raw",
    "Carrot, raw", "Cheese, firm, Danbo, 45 % fidm.", "Chicken, hen, flesh and skin, raw",
    "Chickpeas, canned", "Eggs, chicken, free-range hens (indoor), raw",
    "Milk, whole, 3.5 % fat", "Mushroom, raw", "Onion, raw", "Orange, raw",
    "Potato, raw", "Tomato, ripe, raw, origin unknown", "Oatmilk, with added calcium",
    "Green lentils, dried", "Beef, mince, 10-15% fat, raw", "Lamb, meat, average values, raw",
    "Pork, mince, 5-10% fat, raw", "Yogurt plain, whole milk"
]
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
CONTRADICTIONS = {
    ("walk", "travel"): [("car", "travel"), ("bus", "travel"), ("train", "travel")],
    ("bike", "travel"): [("car", "travel"), ("bus", "travel"), ("train", "travel")],
    ("car", "travel"): [("walk", "travel"), ("bike", "travel")],
    ("bus", "travel"): [("walk", "travel"), ("bike", "travel")],
    ("train", "travel"): [("walk", "travel"), ("bike", "travel")],
}

challenge_specs = [
    ("Personal", "Cycle & Walk Week", 40, 55, "Log low-carbon commuting actions. Evidence required for prizes."),
    ("Personal", "Veggie Lunch Sprint", 38, 50, "Submit vegetarian-friendly food swaps. Evidence required."),
    ("Personal", "Laundry Switch-Up", 34, 45, "Use cold wash and air dry more often. Evidence optional."),
    ("Personal", "Zero Waste Week", 28, 40, "Track recycling and composting actions. Evidence required."),
    ("Group", "Hall vs Hall Commute Cup", 42, 55, "Groups compete on verified commuting points. Evidence required."),
    ("Group", "Society Energy Saver", 36, 50, "Reduce heating and lighting use as a team."),
    ("Group", "Circular Campus Challenge", 30, 45, "Recycling-focused team challenge with moderation."),
    ("Group", "Term Finale Carbon League", 24, 40, "Overall seasonal leaderboard challenge across groups."),
]

group_names = [
    "Alder Hall", "Birch Hall", "Cedar Hall", "Dove Society", "Eco Reps",
    "Forest House", "Green Machines", "Harbour House", "Impact Society",
    "Juniper Hall", "Kindred College", "Lighthouse Society",
]

# Insert users and accounts
user_ids = []
account_ids = []
moderator_ids = []
account_details = {}

for i in range(1, NUM_USERS + 1):
    is_moderator = 1 if i <= 12 else 0
    user_type = "staff" if i % 7 == 0 else "student"
    first_name = fake.first_name()
    last_name = fake.last_name()
    email_prefix = "moderator" if is_moderator else "participant"
    username = f"{email_prefix}{i:03d}"
    email = f"{username}@campuscarbon.test"
    course = random.choice(["Computer Science", "Geography", "Business", "Biology", "Engineering"]) if user_type == "student" else None
    department = random.choice(["Sustainability", "IT Services", "Estates", "Registry", "Library"]) if user_type == "staff" else None

    cursor.execute(
        """
        INSERT INTO Users(first_name, last_name, dob, email, user_type, course, department)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            first_name,
            last_name,
            fake.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
            email,
            user_type,
            course,
            department,
        ),
    )
    user_id = cursor.lastrowid
    user_ids.append(user_id)

    created = ts(365 - (i % 120), 9, i % 50, 0)
    last_active = ts(i % 30, 8 + (i % 10), (i * 3) % 60, 0)
    cursor.execute(
        """
        INSERT INTO Accounts(user_id, username, password, is_moderator, date_created, last_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, username, COMMON_TEST_PASSWORD_HASH, is_moderator, created, last_active),
    )
    account_id = cursor.lastrowid
    account_ids.append(account_id)
    if is_moderator:
        moderator_ids.append(account_id)

    account_details[account_id] = {
        "username": username,
        "email": email,
        "role": "moderator" if is_moderator else "participant",
        "user_type": user_type,
        "first_name": first_name,
        "last_name": last_name,
        "groups": [],
    }

# ModRequest
for i in range(TARGET_MOD_REQUESTS):
    requester = account_ids[12 + (i % (NUM_USERS - 12))]
    reviewer = moderator_ids[i % len(moderator_ids)]
    status = ["pending", "approved", "rejected"][i % 3]
    cursor.execute(
        """
        INSERT INTO ModRequest(account_id, reviewed_by, submitted_at, request_status)
        VALUES (?, ?, ?, ?)
        """,
        (requester, reviewer, ts(90 - (i % 60), 10 + (i % 8), (i * 5) % 60, 0), status),
    )

# Groups
group_ids = []
group_leaders = {}
account_group_pairs = set()

member_pool = account_ids[12:] # Mostly non-moderators
rotation_index = 0

for idx, group_name in enumerate(group_names, start=1):
    creator = moderator_ids[(idx - 1) % len(moderator_ids)]
    cursor.execute(
        """
        INSERT INTO UserGroup(group_creator_id, group_name, group_created)
        VALUES (?, ?, ?)
        """,
        (creator, group_name, ts(150 - idx * 3, 11, idx % 50, 0)),
    )
    group_id = cursor.lastrowid
    group_ids.append(group_id)
    group_leaders[group_id] = creator

    cursor.execute(
        """
        INSERT INTO AccountGroup(account_id, group_id, roles, joined)
        VALUES (?, ?, ?, ?)
        """,
        (creator, group_id, "Owner", ts(145 - idx * 3, 12, idx % 50, 0)),
    )
    account_group_pairs.add((creator, group_id))
    account_details[creator]["groups"].append(group_name)

    member_count = 5 + (idx % 4)
    for _ in range(member_count):
        member = member_pool[rotation_index % len(member_pool)]
        rotation_index += 1
        if (member, group_id) in account_group_pairs:
            continue
        cursor.execute(
            """
            INSERT INTO AccountGroup(account_id, group_id, roles, joined)
            VALUES (?, ?, ?, ?)
            """,
            (member, group_id, "Member", ts(140 - idx * 2, 13, rotation_index % 50, 0)),
        )
        account_group_pairs.add((member, group_id))
        account_details[member]["groups"].append(group_name)

# Reverse lookup: account -> groups
account_to_groups = defaultdict(list)
for account_id, group_id in account_group_pairs:
    account_to_groups[account_id].append(group_id)

# ActionType
action_type_meta = {}
action_lookup = {}
for action_name, category, unit, factor in action_types:
    cursor.execute(
        """
        INSERT INTO ActionType(actionName, category, unit, co2e_factor)
        VALUES (?, ?, ?, ?)
        """,
        (action_name, category, unit, factor),
    )
    action_id = cursor.lastrowid
    action_type_meta[action_id] = {
        "actionName": action_name,
        "category": category,
        "unit": unit,
        "co2e_factor": factor,
    }
    action_lookup[(action_name, category)] = action_id

# Challenges
challenge_ids = []
challenge_meta = {}

for i, (challenge_type, title, start_days_ago, duration_days, rules) in enumerate(challenge_specs, start=1):
    start_dt = dt(start_days_ago, 8 + (i % 5), 0, 0)
    end_dt = start_dt + timedelta(days=duration_days)
    created_by = moderator_ids[(i - 1) % len(moderator_ids)]
    cursor.execute(
        """
        INSERT INTO Challenge(created_by, challenge_type, title, start_date, end_date, rules)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (created_by, challenge_type, title, start_dt.strftime("%Y-%m-%d %H:%M:%S"), end_dt.strftime("%Y-%m-%d %H:%M:%S"), rules),
    )
    challenge_id = cursor.lastrowid
    challenge_ids.append(challenge_id)
    challenge_meta[challenge_id] = {
        "challenge_type": challenge_type,
        "title": title,
        "start": start_dt,
        "end": end_dt,
    }

# IndividualParticipation
individual_pairs = set()
challenge_to_individual_accounts = defaultdict(list)

personal_candidates = account_ids[12:]
for idx, challenge_id in enumerate(challenge_ids[:4], start=1):
    participants = personal_candidates[(idx - 1) * 14: (idx - 1) * 14 + 24]
    if len(participants) < 18:
        participants = personal_candidates[:24]
    for offset, account_id in enumerate(participants):
        joined = (challenge_meta[challenge_id]["start"] - timedelta(days=2 + (offset % 4))).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO IndividualParticipation(challenge_id, account_id, joined_date)
            VALUES (?, ?, ?)
            """,
            (challenge_id, account_id, joined),
        )
        individual_pairs.add((challenge_id, account_id))
        challenge_to_individual_accounts[challenge_id].append(account_id)

# 9. GroupParticipation
group_pairs = set()
challenge_to_groups = defaultdict(list)
for idx, challenge_id in enumerate(challenge_ids[4:], start=1):
    participating_groups = group_ids[: 6 + (idx % 3)]
    for offset, group_id in enumerate(participating_groups):
        joined = (challenge_meta[challenge_id]["start"] - timedelta(days=3 + (offset % 3))).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO GroupParticipation(challenge_id, group_id, joined_date)
            VALUES (?, ?, ?)
            """,
            (challenge_id, group_id, joined),
        )
        group_pairs.add((challenge_id, group_id))
        challenge_to_groups[challenge_id].append(group_id)

# Helpers
log_ids = []
log_owner = {}
log_datetime = {}
log_category = {}
log_action_name = {}
log_quantity = {}
edge_case_log_ids = []
seed_scenarios = []


def add_seed_scenario(code: str, scenario_type: str, ref_table: str, ref_id: int, description: str):
    seed_scenarios.append((code, scenario_type, ref_table, ref_id, description))


def insert_action_log(account_id: int, action_name: str, category: str, quantity, log_dt: datetime, *, edge_code: str | None = None, description: str | None = None):
    action_id = action_lookup[(action_name, category)]
    factor = action_type_meta[action_id]["co2e_factor"]
    if category == "food" and isinstance(quantity, list):
        quantity_text = " ".join(f"{name}:{kg}" for name, kg in quantity)
        co2e_saved = round(sum(action_type_meta[action_lookup[(name, "food")]]["co2e_factor"] * float(kg) for name, kg in quantity), 3)
        action_id = action_lookup[(quantity[-1][0], "food")]
        stored_quantity = quantity_text
    else:
        q = float(quantity)
        stored_quantity = f"{q:.2f}".rstrip("0").rstrip(".") if not float(q).is_integer() else str(int(q))
        co2e_saved = round(q * factor, 3)
    cursor.execute(
        """
        INSERT INTO ActionLog(submitted_by, actionType_id, log_date, quantity, co2e_saved)
        VALUES (?, ?, ?, ?, ?)
        """,
        (account_id, action_id, log_dt.strftime("%Y-%m-%d %H:%M:%S"), stored_quantity, co2e_saved),
    )
    log_id = cursor.lastrowid
    log_ids.append(log_id)
    log_owner[log_id] = account_id
    log_datetime[log_id] = log_dt
    log_category[log_id] = category
    log_action_name[log_id] = action_name
    log_quantity[log_id] = stored_quantity
    if edge_code:
        edge_case_log_ids.append(log_id)
        add_seed_scenario(edge_code, "edge_case_submission", "ActionLog", log_id, description or edge_code)
    return log_id

# ActionLog
# Normal Logs
for i in range(TARGET_NORMAL_ACTION_LOGS):
    account_id = account_ids[i % len(account_ids)]
    bucket = i % 20
    if bucket < 7:
        category = "travel"
        action_name = TRAVEL_ACTIONS[(i + account_id) % len(TRAVEL_ACTIONS)]
        qty = round(random.uniform(0.8, 14.0), 1)
    elif bucket < 11:
        category = "energy"
        action_name = ENERGY_ACTIONS[(i + account_id) % len(ENERGY_ACTIONS)]
        qty = round(random.uniform(1.0, 5.0), 1)
    elif bucket < 15:
        category = "waste"
        action_name = WASTE_ACTIONS[(i + account_id) % len(WASTE_ACTIONS)]
        qty = round(random.uniform(0.2, 3.5), 1)
    else:
        category = "food"
        foods = random.sample(FOOD_ACTIONS, 2 + (i % 2))
        qty = [(food, round(random.uniform(0.1, 0.8), 2)) for food in foods]
        action_name = foods[-1]
    log_dt = BASE_NOW - timedelta(days=random.randint(1, 88), hours=random.randint(0, 12), minutes=random.randint(0, 59))
    insert_action_log(account_id, action_name, category, qty, log_dt)

# Edge cases: Duplicates (24 logs)
for case_idx in range(12):
    account_id = account_ids[15 + case_idx]
    action_name = "bike" if case_idx % 2 == 0 else "lights"
    category = "travel" if action_name == "bike" else "energy"
    base_dt = dt(20 - case_idx, 8, 15, 0)
    qty = 4 if action_name == "bike" else 3
    insert_action_log(account_id, action_name, category, qty, base_dt, edge_code="duplicate_submission", description="Original submission in duplicate-pair scenario.")
    insert_action_log(account_id, action_name, category, qty, base_dt + timedelta(seconds=45), edge_code="duplicate_submission", description="Duplicate of the same action within two minutes.")

# Edge cases: Unrealistic frequency (28 logs)
for case_idx in range(4):
    account_id = account_ids[30 + case_idx]
    action_name = ["heating", "cold-wash", "recycle-paper", "walk"][case_idx]
    category = ["energy", "energy", "waste", "travel"][case_idx]
    qty = [2, 1, 1.5, 3][case_idx]
    for burst in range(7):
        insert_action_log(
            account_id,
            action_name,
            category,
            qty,
            dt(12 - case_idx, 7 + burst, 5 * burst, 0),
            edge_code="unrealistic_frequency",
            description=f"Repeated {action_name} action in the same day to exceed the daily limit.",
        )

# Edge cases: Contradictory Logs (20 logs)
contradiction_pairs = [
    ("walk", "travel", "car", "travel"),
    ("bike", "travel", "bus", "travel"),
    ("walk", "travel", "train", "travel"),
    ("bike", "travel", "car", "travel"),
    ("walk", "travel", "bus", "travel"),
    ("bike", "travel", "train", "travel"),
    ("walk", "travel", "car", "travel"),
    ("bike", "travel", "bus", "travel"),
    ("walk", "travel", "train", "travel"),
    ("bike", "travel", "car", "travel"),
]
for idx, (a1, c1, a2, c2) in enumerate(contradiction_pairs):
    account_id = account_ids[40 + idx]
    day = 18 - idx
    insert_action_log(account_id, a1, c1, 3 + (idx % 3), dt(day, 8, 0, 0), edge_code="contradictory_log", description=f"Contradictory pair: {a1} on same day as {a2}.")
    insert_action_log(account_id, a2, c2, 4 + (idx % 2), dt(day, 8, 40, 0), edge_code="contradictory_log", description=f"Contradictory pair: {a2} on same day as {a1}.")

# Edge cases: Suspicious / impossible quantity (16 logs)
quantity_cases = [
    ("walk", "travel", 35, "suspicious_quantity"),
    ("bike", "travel", 150, "impossible_quantity"),
    ("recycle-paper", "waste", 18, "suspicious_quantity"),
    ("recycle-aluminium", "waste", 18, "impossible_quantity"),
    ("heating", "energy", 18, "suspicious_quantity"),
    ("lights", "energy", 30, "impossible_quantity"),
    ("bus", "travel", 140, "suspicious_quantity"),
    ("cold-wash", "energy", 10, "impossible_quantity"),
    ("compost-food", "waste", 9, "suspicious_quantity"),
    ("walk", "travel", 0.05, "suspicious_quantity"),
    ("recycle-glass", "waste", 40, "impossible_quantity"),
    ("bike", "travel", 45, "suspicious_quantity"),
    ("heating", "energy", 28, "impossible_quantity"),
    ("recycle-plastic", "waste", 12, "suspicious_quantity"),
    ("train", "travel", 500, "impossible_quantity"),
    ("lights", "energy", 0.1, "suspicious_quantity"),
]
for idx, (action_name, category, qty, code) in enumerate(quantity_cases):
    account_id = account_ids[55 + (idx % 12)]
    insert_action_log(account_id, action_name, category, qty, dt(10 - (idx % 7), 15, idx * 3 % 60, 0), edge_code=code, description=f"Quantity edge case for {action_name}: {qty}.")

# Edge cases: Reused evidence candidates (12 logs)
reused_evidence_log_ids = []
for idx in range(12):
    account_id = account_ids[20 + idx]
    action_name = ["recycle-paper", "bike", "lights"][idx % 3]
    category = ["waste", "travel", "energy"][idx % 3]
    qty = [1.2, 5, 2.5][idx % 3]
    log_id = insert_action_log(account_id, action_name, category, qty, dt(8 - (idx % 5), 10, idx * 4 % 60, 0), edge_code="reused_evidence", description="Submission designed to reuse an evidence file hash.")
    reused_evidence_log_ids.append(log_id)

# Edge cases: Challenge farming candidates (20 logs)
challenge_farming_log_ids = []
farmer_accounts = account_ids[70:74]
for idx, account_id in enumerate(farmer_accounts):
    for rep in range(5):
        log_id = insert_action_log(account_id, "lights", "energy", 2, dt(6 - idx, 17, rep * 6, 0), edge_code="challenge_farming", description="Repeated same-action challenge submissions for farming detection.")
        challenge_farming_log_ids.append(log_id)

assert len(log_ids) >= 500, f"Expected at least 500 action logs, got {len(log_ids)}"
assert len(edge_case_log_ids) >= 100, f"Expected at least 100 edge case logs, got {len(edge_case_log_ids)}"

# ChallengeAction
challenge_action_ids = []
challenge_action_to_log = {}
used_pairs = set()

account_logs_by_owner = defaultdict(list)
for log_id in log_ids:
    account_logs_by_owner[log_owner[log_id]].append(log_id)

logs_by_group = defaultdict(list)
for account_id, groups in account_to_groups.items():
    for gid in groups:
        logs_by_group[gid].extend(account_logs_by_owner.get(account_id, []))

# Personal challenges - Include farming edge case logs in first personal challenge
personal_targets = [60, 60, 55, 55]
for idx, challenge_id in enumerate(challenge_ids[:4]):
    valid_accounts = challenge_to_individual_accounts[challenge_id]
    if idx == 0:
        for account_id in farmer_accounts:
            if account_id not in valid_accounts:
                valid_accounts.append(account_id)
                cursor.execute(
                    "INSERT INTO IndividualParticipation(challenge_id, account_id, joined_date) VALUES (?, ?, ?)",
                    (challenge_id, account_id, (challenge_meta[challenge_id]["start"] - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),
                )
    candidate_logs = []
    for account_id in valid_accounts:
        candidate_logs.extend(account_logs_by_owner.get(account_id, []))
    candidate_logs = sorted(set(candidate_logs), key=lambda lid: log_datetime[lid])
    random.shuffle(candidate_logs)
    selected = candidate_logs[: personal_targets[idx]]
    if idx == 0:
        # Ensure challenge farming logs are in challenge 1
        selected = list(dict.fromkeys(challenge_farming_log_ids + selected))[: personal_targets[idx]]
    for pos, log_id in enumerate(selected):
        if (challenge_id, log_id) in used_pairs:
            continue
        used_pairs.add((challenge_id, log_id))
        points = 10 + (pos % 25)
        cursor.execute(
            "INSERT INTO ChallengeAction(challenge_id, group_id, log_id, point_awarded) VALUES (?, ?, ?, ?)",
            (challenge_id, None, log_id, points),
        )
        ca_id = cursor.lastrowid
        challenge_action_ids.append(ca_id)
        challenge_action_to_log[ca_id] = log_id

# Group Challenges
for idx, challenge_id in enumerate(challenge_ids[4:]):
    group_list = challenge_to_groups[challenge_id]
    per_group = 8 + idx
    for group_id in group_list:
        candidate_logs = sorted(set(logs_by_group[group_id]), key=lambda lid: log_datetime[lid])
        random.shuffle(candidate_logs)
        selected = candidate_logs[:per_group]
        for pos, log_id in enumerate(selected):
            if (challenge_id, log_id) in used_pairs:
                continue
            used_pairs.add((challenge_id, log_id))
            points = 12 + ((group_id + pos) % 20)
            cursor.execute(
                "INSERT INTO ChallengeAction(challenge_id, group_id, log_id, point_awarded) VALUES (?, ?, ?, ?)",
                (challenge_id, group_id, log_id, points),
            )
            ca_id = cursor.lastrowid
            challenge_action_ids.append(ca_id)
            challenge_action_to_log[ca_id] = log_id

assert len(challenge_action_ids) >= TARGET_CHALLENGE_ACTIONS, f"Expected at least {TARGET_CHALLENGE_ACTIONS} challenge submissions, got {len(challenge_action_ids)}"

# Evidence
evidence_ids = []
evidence_for_log = defaultdict(list)
reused_hashes = [hash_value(f"shared-evidence-{i}") for i in range(1, 5)]
reused_urls = [f"https://evidence.example/shared/{i}.jpg" for i in range(1, 5)]

candidate_evidence_logs = list(dict.fromkeys(
    [challenge_action_to_log[ca_id] for ca_id in challenge_action_ids] + reused_evidence_log_ids + edge_case_log_ids + log_ids
))

for idx, log_id in enumerate(candidate_evidence_logs[:TARGET_EVIDENCE]):
    if idx < len(reused_evidence_log_ids):
        url = reused_urls[idx % len(reused_urls)]
        file_hash = reused_hashes[idx % len(reused_hashes)]
        ev_type = ["photo", "receipt", "screenshot"][idx % 3]
    else:
        url = f"https://evidence.example/submission/{log_id}_{idx}.jpg"
        file_hash = hash_value(url)
        ev_type = ["photo", "receipt", "screenshot"][idx % 3]
    ev_dt = (log_datetime[log_id] + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO Evidence(log_id, evidence_type, evidence_url, evidence_date, file_hash)
        VALUES (?, ?, ?, ?, ?)
        """,
        (log_id, ev_type, url, ev_dt, file_hash),
    )
    evidence_id = cursor.lastrowid
    evidence_ids.append(evidence_id)
    evidence_for_log[log_id].append(evidence_id)
    if log_id in reused_evidence_log_ids:
        add_seed_scenario("reused_evidence", "evidence_edge_case", "Evidence", evidence_id, "Evidence intentionally reuses a shared file hash for testing duplicate-evidence detection.")

# Decisions: 70 total, with 50 resolved and 20 pending
for idx, evidence_id in enumerate(evidence_ids[:TARGET_DECISIONS]):
    reviewer_id = moderator_ids[idx % len(moderator_ids)]
    if idx < 30:
        status = "approved"
        reason = "Evidence verified and submission accepted."
        decision_date = ts(5 + (idx % 20), 15, idx % 60, 0)
    elif idx < 50:
        status = "rejected"
        reason = "Evidence invalid, contradictory, or duplicate."
        decision_date = ts(4 + (idx % 20), 16, idx % 60, 0)
    else:
        status = "pending"
        reason = "Awaiting moderator review for flagged or sampled submission."
        decision_date = None
    cursor.execute(
        """
        INSERT INTO Decision(evidence_id, reviewer_id, decision_status, decision_date, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        (evidence_id, reviewer_id, status, decision_date, reason),
    )
    if status == "rejected":
        add_seed_scenario("moderation_rejection", "moderation_case", "Decision", cursor.lastrowid, "Rejected moderation example for invalid or duplicate evidence.")
    elif status == "pending":
        add_seed_scenario("moderation_pending", "moderation_case", "Decision", cursor.lastrowid, "Pending moderation example for review queues.")

# Anti-gaming flags for edge cases
flag_rows = []
review_samples = []

# Duplicate flags on second log in each pair
for i in range(1, 24, 2):
    log_id = edge_case_log_ids[i]
    account_id = log_owner[log_id]
    flag_rows.append((log_id, account_id, "duplicate_submission", "high", "open", "Same action type and quantity submitted within two minutes.", ts(2, 12, i, 0), None, None))

# Frequency flags on final four logs of each burst
frequency_logs = [lid for lid in edge_case_log_ids if log_action_name[lid] in {"heating", "cold-wash", "recycle-paper", "walk"} and log_datetime[lid].date() in {dt(12).date(), dt(11).date(), dt(10).date(), dt(9).date()}]
for log_id in frequency_logs[-12:]:
    account_id = log_owner[log_id]
    flag_rows.append((log_id, account_id, "unrealistic_frequency", "medium", "reviewed", "User exceeded the seeded daily limit for this action type.", ts(2, 13, log_id % 60, 0), moderator_ids[log_id % len(moderator_ids)], ts(1, 9, log_id % 60, 0)))

# Contradictory flags on second log of each pair
contradiction_log_ids = [lid for lid in edge_case_log_ids if log_datetime[lid].hour in {8} or log_datetime[lid].hour in {8,9}]
start = 24 + 28
contradiction_section = edge_case_log_ids[start:start+20]
# contradictory_log flags removed — check now only applies to ChallengeAction submissions

# Quantity flags
quantity_section = edge_case_log_ids[start+20:start+20+16]
for log_id in quantity_section:
    account_id = log_owner[log_id]
    code = "impossible_quantity" if float(log_quantity[log_id]) > 24 or float(log_quantity[log_id]) > 100 else "suspicious_quantity"
    if log_id in quantity_section[1::2]:
        code = "impossible_quantity"
    flag_rows.append((log_id, account_id, code, "high" if code == "impossible_quantity" else "medium", "open", f"Seeded quantity {log_quantity[log_id]} is outside the expected range for {log_action_name[log_id]}.", ts(2, 15, log_id % 60, 0), None, None))

# Reused evidence flags
for log_id in reused_evidence_log_ids[:8]:
    account_id = log_owner[log_id]
    flag_rows.append((log_id, account_id, "reused_evidence", "medium", "open", "Evidence hash is intentionally shared with another seeded submission.", ts(2, 16, log_id % 60, 0), None, None))

# Challenge farming flags
for log_id in challenge_farming_log_ids[:8]:
    account_id = log_owner[log_id]
    flag_rows.append((log_id, account_id, "challenge_farming", "medium", "open", "High proportion of challenge submissions are the same action type.", ts(2, 17, log_id % 60, 0), None, None))

for row in flag_rows:
    cursor.execute(
        """
        INSERT INTO AntiGamingFlag(action_log_id, account_id, rule_code, severity, status, reason, created_at, reviewed_by, reviewed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        row,
    )
    add_seed_scenario(row[2], "antigaming_flag", "AntiGamingFlag", cursor.lastrowid, row[5])


# Badge test: seed one user with 180 consecutive days of challenge submissions
# This lets you immediately verify all 4 badge tiers (week/month/super/legend)
streak_account_id = account_ids[12]
streak_challenge_id = challenge_ids[0]
walk_action_id = action_lookup[("walk", "travel")]
walk_factor = action_type_meta[walk_action_id]["co2e_factor"]

for day_offset in range(180):
    log_dt = BASE_NOW - timedelta(days=179 - day_offset)
    log_dt = log_dt.replace(hour=8, minute=0, second=0)
    quantity = 5
    co2e = round(quantity * walk_factor, 3)
    cursor.execute(
        "INSERT INTO ActionLog(submitted_by, actionType_id, log_date, quantity, co2e_saved) VALUES (?, ?, ?, ?, ?)",
        (streak_account_id, walk_action_id, log_dt.strftime("%Y-%m-%d %H:%M:%S"), quantity, co2e),
    )
    streak_log_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO ChallengeAction(challenge_id, group_id, log_id, point_awarded) VALUES (?, ?, ?, ?)",
        (streak_challenge_id, None, streak_log_id, co2e),
    )

# Seed badges for participant013 based on their 180-day streak
badge_now = BASE_NOW.strftime("%Y-%m-%d %H:%M:%S")
for days_needed, badge_type in [(7, "week"), (30, "month"), (60, "super"), (180, "legend")]:
    cursor.execute(
        "INSERT OR IGNORE INTO UserBadge(account_id, badge_type, awarded_at) VALUES (?, ?, ?)",
        (streak_account_id, badge_type, badge_now),
    )

# Summary
conn.commit()

# Table counts
cursor.execute("SELECT COUNT(*) FROM Users")
users_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM Accounts")
accounts_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM ModRequest")
modrequest_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM UserGroup")
groups_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM AccountGroup")
accountgroup_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM ActionType")
actiontype_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM ActionLog")
actionlog_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM Challenge")
challenge_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM IndividualParticipation")
individual_participation_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM GroupParticipation")
group_participation_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM ChallengeAction")
challengeaction_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM Evidence")
evidence_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM Decision")
decision_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM AntiGamingFlag")
antigamingflag_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM AntiGamingRule")
antigamingrule_count = cursor.fetchone()[0]

# Requirement summary
print("\n=== Requirement Summary ===")
print(f"Users (>= 60): {users_count}")
print(f"Groups (>= 10): {groups_count}")
print(f"Action logs (>= 500): {actionlog_count}")
print(f"Challenges (>= 8): {challenge_count}")
print(f"Challenge submissions / ChallengeAction (>= 200): {challengeaction_count}")
print(f"Evidence submissions (>= 80): {evidence_count}")
print(f"Moderation decisions (>= 40): {decision_count}")
print(f"Pre-seeded edge-case submissions (>= 100): {len(edge_case_log_ids)}")

# Extra context
print("\n=== Extra Dataset Counts ===")
print(f"Accounts: {accounts_count}")
print(f"Moderator requests: {modrequest_count}")
print(f"Account-group memberships: {accountgroup_count}")
print(f"Action types: {actiontype_count}")
print(f"IndividualParticipation rows: {individual_participation_count}")
print(f"GroupParticipation rows: {group_participation_count}")
print(f"AntiGamingFlag rows: {antigamingflag_count}")
print(f"AntiGamingRule rows: {antigamingrule_count}")

# Sanity assertions for marking requirements
assert users_count >= 60, f"Expected at least 60 users, got {users_count}"
assert groups_count >= 10, f"Expected at least 10 groups, got {groups_count}"
assert actionlog_count >= 500, f"Expected at least 500 action logs, got {actionlog_count}"
assert challenge_count >= 8, f"Expected at least 8 challenges, got {challenge_count}"
assert challengeaction_count >= 200, f"Expected at least 200 challenge submissions, got {challengeaction_count}"
assert evidence_count >= 80, f"Expected at least 80 evidence submissions, got {evidence_count}"
assert decision_count >= 40, f"Expected at least 40 moderation decisions, got {decision_count}"
assert len(edge_case_log_ids) >= 100, f"Expected at least 100 edge-case submissions, got {len(edge_case_log_ids)}"

# Helpful login output
print("\n=== Common Login Details ===")
print(f"Common test password: {COMMON_TEST_PASSWORD}")

print("\nSample moderator accounts:")
for aid in moderator_ids[:5]:
    details = account_details[aid]
    print(f"- username: {details['username']} | email: {details['email']} | role: {details['role']}")

print("\nSample participant accounts:")
participant_sample = [aid for aid in account_ids if aid not in moderator_ids][:5]
for aid in participant_sample:
    details = account_details[aid]
    print(f"- username: {details['username']} | email: {details['email']} | role: {details['role']}")

print("\nSeeding complete.")

conn.close()