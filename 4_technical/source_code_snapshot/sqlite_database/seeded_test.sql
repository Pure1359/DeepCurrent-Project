SELECT 
  (SELECT COUNT(*) FROM Users) AS users,
  (SELECT COUNT(*) FROM Accounts) AS accounts,
  (SELECT COUNT(*) FROM ActionLog) AS logs,
  (SELECT COUNT(*) FROM Challenge) AS challenges,
  (SELECT COUNT(*) FROM Evidence) AS evidence,
  (SELECT COUNT(*) FROM Decision) AS decisions;