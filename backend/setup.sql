-- Run this once as a MySQL administrator (root), then use the codeher_app
-- credentials in backend/.env. Django never needs the root password.
--
-- PowerShell example:
--   & "C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe" -u root -p -e "source setup.sql"

CREATE DATABASE IF NOT EXISTS codeher
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'codeher_app'@'localhost' IDENTIFIED BY 'REPLACE_WITH_A_STRONG_PASSWORD';
CREATE USER IF NOT EXISTS 'codeher_app'@'127.0.0.1' IDENTIFIED BY 'REPLACE_WITH_A_STRONG_PASSWORD';

-- Django creates and drops test_* schemas when it runs the automated tests.
-- The suite itself is pinned to SQLite (config/test_settings.py), so these
-- grants are enough for normal use; giving an app user CREATE ON *.* purely to
-- let it build its own test schema is not recommended on a shared server.
GRANT ALL PRIVILEGES ON codeher.* TO 'codeher_app'@'localhost';
GRANT ALL PRIVILEGES ON codeher.* TO 'codeher_app'@'127.0.0.1';
GRANT CREATE, ALTER, DROP, INDEX ON codeher.* TO 'codeher_app'@'localhost';
GRANT CREATE, ALTER, DROP, INDEX ON codeher.* TO 'codeher_app'@'127.0.0.1';

FLUSH PRIVILEGES;
