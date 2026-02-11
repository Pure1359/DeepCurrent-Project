CREATE TABLE "AccountGroup" (
        "account_id" INTEGER NULL  ,
        "group_id" INTEGER NULL  ,
        "roles" VARCHAR(50) NULL  ,
        "joined" DATETIME NULL,
        FOREIGN KEY("account_id") REFERENCES "Accounts" ("account_id") ON UPDATE NO ACTION ON DELETE NO ACTION,
        FOREIGN KEY("group_id") REFERENCES "UserGroup" ("group_id") ON UPDATE NO ACTION ON DELETE NO ACTION
);


CREATE TABLE "Accounts" (
        "account_id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "user_id" INTEGER NOT NULL  ,
        "username" VARCHAR(50) NOT NULL  ,
        "password" VARCHAR(200) NOT NULL  ,
        "is_moderator" TINYINT NULL  ,
        "date_created" DATETIME NULL  ,
        "last_active" DATETIME NULL,
        FOREIGN KEY("user_id") REFERENCES "Users" ("user_id") ON UPDATE NO ACTION ON DELETE NO ACTION
);


CREATE TABLE sqlite_sequence(name,seq)


CREATE TABLE "ActionLog" (
        "log_id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "submitted_by" INTEGER NULL  ,
        "actionType_id" INTEGER NULL  ,
        "log_date" DATETIME NULL  ,
        "quantity" INTEGER NULL  ,
        "co2e_saved" FLOAT NULL,
        FOREIGN KEY("submitted_by") REFERENCES "Accounts" ("account_id") ON UPDATE NO ACTION ON DELETE NO ACTION,
        FOREIGN KEY("actionType_id") REFERENCES "ActionType" ("actionType_id") ON UPDATE NO ACTION ON DELETE NO ACTION
);


CREATE TABLE "ActionType" (
        "actionType_id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "actionName" VARCHAR(50) NULL  ,
        "category" VARCHAR(50) NULL  ,
        "unit" VARCHAR(5) NULL  ,
        "co2e_factor" FLOAT NULL
);


CREATE TABLE "Challenge" (
        "challenge_id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "created_by" INTEGER NULL  ,
        "challenge_type" VARCHAR(50) NULL  ,
        "title" VARCHAR(50) NULL  ,
        "start_date" DATETIME NULL  ,
        "end_date" DATETIME NULL  ,
        "rules" TEXT NULL,
        FOREIGN KEY("created_by") REFERENCES "Accounts" ("account_id") ON UPDATE NO ACTION ON DELETE NO ACTION
);


CREATE TABLE "ChallengeAction" (
        "challengeAction_id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "challenge_id" INTEGER NULL  ,
        "group_id" INTEGER NULL  ,
        "log_id" INTEGER NULL  ,
        "point_awarded" INTEGER NULL,
        FOREIGN KEY("challenge_id") REFERENCES "Challenge" ("challenge_id") ON UPDATE NO ACTION ON DELETE NO ACTION,
        FOREIGN KEY("group_id") REFERENCES "UserGroup" ("group_id") ON UPDATE NO ACTION ON DELETE NO ACTION,
        FOREIGN KEY("log_id") REFERENCES "ActionLog" ("log_id") ON UPDATE NO ACTION ON DELETE NO ACTION
);


CREATE TABLE "Decision" (
        "decision_id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "evidence_id" INTEGER NULL  ,
        "reviewer_id" INTEGER NULL  ,
        "decision_status" VARCHAR(50) NULL  ,
        "decision_date" DATETIME NULL  ,
        "reason" TEXT NULL,
        FOREIGN KEY("evidence_id") REFERENCES "Evidence" ("evidence_id") ON UPDATE NO ACTION ON DELETE NO ACTION,
        FOREIGN KEY("reviewer_id") REFERENCES "Accounts" ("account_id") ON UPDATE NO ACTION ON DELETE NO ACTION
);


CREATE TABLE "Evidence" (
        "evidence_id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "log_id" INTEGER NULL  ,
        "evidence_type" VARCHAR(50) NULL  ,
        "evidence_url" TEXT NULL  ,
        "evidence_date" DATETIME NULL,
        FOREIGN KEY("log_id") REFERENCES "ActionLog" ("log_id") ON UPDATE NO ACTION ON DELETE NO ACTION
);


CREATE TABLE "GroupParticipation" (
        "challenge_id" INTEGER NULL  ,
        "group_id" INTEGER NULL  ,
        "joined_date" DATETIME NULL,
        FOREIGN KEY("challenge_id") REFERENCES "Challenge" ("challenge_id") ON UPDATE NO ACTION ON DELETE NO ACTION,
        FOREIGN KEY("group_id") REFERENCES "UserGroup" ("group_id") ON UPDATE NO ACTION ON DELETE NO ACTION
);


CREATE TABLE "IndividualParticipation" (
        "challenge_id" INTEGER NULL  ,
        "account_id" INTEGER NULL  ,
        "joined_date" DATETIME NULL,
        FOREIGN KEY("challenge_id") REFERENCES "Challenge" ("challenge_id") ON UPDATE NO ACTION ON DELETE NO ACTION,
        FOREIGN KEY("account_id") REFERENCES "Accounts" ("account_id") ON UPDATE NO ACTION ON DELETE NO ACTION
);


CREATE TABLE "ModRequest" (
        "req_id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "account_id" INTEGER NULL  ,
        "reviewed_by" INTEGER NULL  ,
        "submitted_at" DATETIME NULL  ,
        "request_status" VARCHAR(50) NULL,
        FOREIGN KEY("account_id") REFERENCES "Accounts" ("account_id") ON UPDATE NO ACTION ON DELETE NO ACTION,
        FOREIGN KEY("reviewed_by") REFERENCES "Accounts" ("account_id") ON UPDATE NO ACTION ON DELETE NO ACTION
);


CREATE TABLE "UserGroup" (
        "group_id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "group_creator_id" INTEGER NULL  ,
        "group_name" VARCHAR(50) NULL  ,
        "group_created" DATETIME NULL,
        FOREIGN KEY("group_creator_id") REFERENCES "Accounts" ("account_id") ON UPDATE NO ACTION ON DELETE NO ACTION
);


CREATE TABLE "Users" (
        "user_id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "first_name" VARCHAR(50) NOT NULL  ,
        "last_name" VARCHAR(50) NOT NULL  ,
        "dob" DATE NULL  ,
        "email" VARCHAR(50) NOT NULL  ,
        "user_type" VARCHAR(50) NOT NULL  ,
        "course" VARCHAR(50) NULL  ,
        "department" VARCHAR(50) NULL
);