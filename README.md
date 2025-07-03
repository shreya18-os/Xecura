# Xecura Discord Bot

## Data Storage

User data (badges and no-prefix status) is stored in a SQLite database (`data.db`) and is automatically managed by the bot. The SQLite database provides:

- ACID compliance (Atomicity, Consistency, Isolation, Durability)
- Transactional safety
- Better data integrity
- Concurrent access handling
- Automatic data corruption prevention

### Database Schema

```sql
-- Badges table stores user badges
CREATE TABLE badges (
    user_id TEXT,
    badge TEXT,
    PRIMARY KEY (user_id, badge)
);

-- No-prefix users table stores users with no-prefix privilege
CREATE TABLE no_prefix_users (
    user_id TEXT PRIMARY KEY
);
```

## Features

- Badge system for users
- No-prefix command support for privileged users
- Automatic data saving and consistency verification
- Robust error handling and recovery
