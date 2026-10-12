#!/usr/bin/env python2.7
import sqlite3, os

with open('./.pathToAP', 'r') as f:
    pathToAP = f.readline().strip()

dbPath = os.path.join(pathToAP, 'youtube.db')
db = sqlite3.connect(dbPath)

cols = [row[1] for row in db.execute('PRAGMA table_info(seen)')]
print 'Kolumny seen:', cols

if cols and 'query' not in cols:
    db.execute('DROP TABLE seen')
    db.execute('''CREATE TABLE seen (
        id TEXT,
        query TEXT,
        seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id, query)
    )''')
    db.commit()
    print 'OK - tabela seen zmigrowana'
elif not cols:
    db.execute('''CREATE TABLE seen (
        id TEXT,
        query TEXT,
        seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id, query)
    )''')
    db.commit()
    print 'OK - tabela seen utworzona'
else:
    print 'OK - tabela seen juz ma kolumne query, nic nie zmieniono'

cols_fav = [row[1] for row in db.execute('PRAGMA table_info(favourites)')]
print 'Kolumny favourites:', cols_fav

if cols_fav and 'status' not in cols_fav:
    db.execute("ALTER TABLE favourites ADD COLUMN status TEXT NOT NULL DEFAULT 'active'")
    db.execute("UPDATE favourites SET status='active' WHERE status IS NULL OR status=''")
    db.commit()
    print 'OK - dodano kolumne status do favourites'
else:
    print 'OK - kolumna status juz istnieje lub tabela pusta'

db.close()