# Deterministic industrial telemetry dataset and SQL-first data-quality checks.
import csv
import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

RULES = {
    "missing_reading": "reading IS NULL",
    "out_of_range": "reading IS NOT NULL AND (reading < 0 OR reading > 120)",
    "unknown_sensor": "sensor_id NOT IN (SELECT sensor_id FROM sensors)",
    "duplicate_event": "event_id IN (SELECT event_id FROM readings GROUP BY event_id HAVING COUNT(*) > 1)",
    "future_timestamp": "recorded_at > '2026-11-19T00:00:00'",
}

def connect(path):
    db=sqlite3.connect(str(path))
    db.row_factory=sqlite3.Row
    return db

def initialize(db):
    db.executescript('''DROP TABLE IF EXISTS readings; DROP TABLE IF EXISTS sensors;
    CREATE TABLE sensors(sensor_id INTEGER PRIMARY KEY, plant TEXT NOT NULL, kind TEXT NOT NULL);
    CREATE TABLE readings(row_id INTEGER PRIMARY KEY, event_id INTEGER NOT NULL,
      sensor_id INTEGER NOT NULL, recorded_at TEXT NOT NULL, reading REAL);
    CREATE INDEX idx_readings_sensor ON readings(sensor_id);
    CREATE INDEX idx_readings_event ON readings(event_id);
    ''')
    db.executemany('INSERT INTO sensors VALUES (?,?,?)',
      [(i, ['Budapest','Vienna','Prague'][i%3], ['Temperature','Pressure','Vibration'][i%3]) for i in range(1,31)])
    db.commit()

def seed(db, count=12000, seed=42):
    rng=random.Random(seed)
    start=datetime(2026,10,1)
    batch=[]
    for i in range(1,count+1):
        sensor=rng.randint(1,30)
        timestamp=(start+timedelta(minutes=i*3)).isoformat()
        value=round(rng.gauss(62,17),2)
        event=i
        # Intentional overlapping defects; category totals must not be summed.
        if i%43==0: value=None
        if i%59==0: value=145.0
        if i%71==0: sensor=999
        if i%83==0: event=i-1
        if i%97==0: timestamp='2027-01-15T12:00:00'
        batch.append((i,event,sensor,timestamp,value))
    db.executemany('INSERT INTO readings VALUES (?,?,?,?,?)',batch)
    db.commit()

def quality_results(db):
    total=db.execute('SELECT COUNT(*) FROM readings').fetchone()[0]
    results={}
    for name,condition in RULES.items():
        results[name]=db.execute(f'SELECT COUNT(*) FROM readings WHERE {condition}').fetchone()[0]
    combined=' OR '.join('('+x+')' for x in RULES.values())
    invalid=db.execute(f'SELECT COUNT(*) FROM readings WHERE {combined}').fetchone()[0]
    return {'total':total,'valid':total-invalid,'invalid':invalid,'score':round((total-invalid)/total*100,2) if total else 100.0,'rules':results}

def trend(db):
    conditions=' OR '.join('('+x+')' for x in RULES.values())
    return [dict(r) for r in db.execute(f'''SELECT substr(recorded_at,1,10) AS day,
      COUNT(*) AS total, SUM(CASE WHEN {conditions} THEN 1 ELSE 0 END) AS invalid
      FROM readings GROUP BY substr(recorded_at,1,10) ORDER BY day''')]

def plant_summary(db):
    conditions=' OR '.join('('+x.replace('sensor_id NOT IN', 'r.sensor_id NOT IN')+')' for x in RULES.values())
    return [dict(r) for r in db.execute(f'''SELECT s.plant, COUNT(*) AS total,
      SUM(CASE WHEN {conditions} THEN 1 ELSE 0 END) AS invalid
      FROM readings r JOIN sensors s ON s.sensor_id=r.sensor_id
      GROUP BY s.plant ORDER BY s.plant''')]

def flagged_rows(db,limit=100):
    combined=' OR '.join('('+x+')' for x in RULES.values())
    return [dict(r) for r in db.execute(f'''SELECT row_id,event_id,sensor_id,recorded_at,reading
       FROM readings WHERE {combined} ORDER BY row_id LIMIT ?''',(limit,))]

def export_report(db,path):
    result=quality_results(db)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

def export_flagged_csv(db,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['row_id','event_id','sensor_id','recorded_at','reading'])
        writer.writeheader();writer.writerows(flagged_rows(db,1000000))
