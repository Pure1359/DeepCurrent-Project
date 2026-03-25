SELECT 
  (SELECT COUNT(*) FROM Users) AS users,
  (SELECT COUNT(*) FROM Accounts) AS accounts,
  (SELECT COUNT(*) FROM AccountGroup) AS accountGroup,
  (SELECT COUNT(*) FROM ActionType) AS actionType,
  (SELECT COUNT(*) FROM ChallengeAction) AS challengeAction,
  (SELECT COUNT(*) FROM GroupParticipation) AS groupParticipation, 
  (SELECT COUNT(*) FROM IndividualParticipation) AS indivPart,
  (SELECT COUNT(*) FROM ModRequest) AS modeReq,
  (SELECT COUNT(*) FROM UserGroup) AS userGroup,
  (SELECT COUNT(*) FROM ActionLog) AS logs,
  (SELECT COUNT(*) FROM Challenge) AS challenges,
  (SELECT COUNT(*) FROM Evidence) AS evidence,
  (SELECT COUNT(*) FROM Decision) AS decisions;