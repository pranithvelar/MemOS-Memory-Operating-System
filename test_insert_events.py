import os
import sqlite3
import datetime
import uuid
from src.config.settings import IntelligentMemoryConfig

config = IntelligentMemoryConfig.load()
db_path = os.path.join(config.workspace_dir, 'memory.db')
conn = sqlite3.connect(db_path)

now = datetime.datetime.now(datetime.timezone.utc)
in_1h = now + datetime.timedelta(minutes=60)
in_15m = now + datetime.timedelta(minutes=15)

conn.execute(
    "INSERT INTO facts (id, content, date_start, date_end, status, created_at) VALUES (?, ?, ?, ?, 'active', ?)",
    (str(uuid.uuid4()), 'Important Founder Meeting', in_1h.isoformat(), (in_1h + datetime.timedelta(minutes=30)).isoformat(), now.isoformat())
)

conn.execute(
    "INSERT INTO facts (id, content, date_start, date_end, status, created_at) VALUES (?, ?, ?, ?, 'active', ?)",
    (str(uuid.uuid4()), 'Quick sync call', in_15m.isoformat(), (in_15m + datetime.timedelta(minutes=15)).isoformat(), now.isoformat())
)

conn.commit()
print('Inserted dummy events for 1h and 15m')
