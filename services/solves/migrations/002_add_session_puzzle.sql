-- 002: every session records which puzzle it is for. All existing sessions were 3x3, so the
-- default fills them in and no row is lost or rewritten by hand.
ALTER TABLE sessions ADD puzzle VARCHAR(20) NOT NULL CONSTRAINT df_sessions_puzzle DEFAULT '3x3';
