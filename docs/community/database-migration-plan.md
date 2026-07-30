# Migration Plan

11B-1 add profile and match requirement tables. 11B-2 teams/members. 11B-3 results/ratings. 11B-4 notifications. Create enums/checks/indexes with each table; backfill no user profile rows. PostgreSQL partial unique indexes may enforce one active captain. Never alter the existing baseline migration; rollbacks drop only new tables after checking historical data.
