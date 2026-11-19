import json
import sqlite3
from src.core import initialize,seed,quality_results,trend,plant_summary,flagged_rows,export_report,export_flagged_csv

def make_db(n=12000):
    db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
    initialize(db);seed(db,n);return db

def test_row_count():
    db=make_db(100);assert quality_results(db)['total']==100

def test_repeatability():
    a=make_db(500);b=make_db(500)
    assert quality_results(a)==quality_results(b)

def test_expected_defects():
    db=make_db();r=quality_results(db)
    assert all(v>0 for v in r['rules'].values())
    assert r['total']==r['valid']+r['invalid']
    assert r['invalid']<=sum(r['rules'].values())

def test_duplicate_detection():
    db=make_db(100)
    assert quality_results(db)['rules']['duplicate_event']>0

def test_empty_dataset():
    db=make_db(0)
    assert quality_results(db)['score']==100.0

def test_trend_totals():
    db=make_db(1000)
    assert sum(x['total'] for x in trend(db))==1000

def test_plant_summary_excludes_unknown_sensors():
    db=make_db(1000)
    assert sum(x['total'] for x in plant_summary(db))<1000

def test_flagged_rows():
    db=make_db(1000)
    assert len(flagged_rows(db,10))==10

def test_report_export(tmp_path):
    db=make_db(100)
    path=tmp_path/'report.json';r=export_report(db,path)
    assert json.loads(path.read_text())==r

def test_csv_export(tmp_path):
    db=make_db(100)
    path=tmp_path/'flagged.csv';export_flagged_csv(db,path)
    assert path.exists() and len(path.read_text().splitlines())>1


def test_new_seed_changes_dataset():
    a=sqlite3.connect(':memory:');a.row_factory=sqlite3.Row
    b=sqlite3.connect(':memory:');b.row_factory=sqlite3.Row
    initialize(a);initialize(b)
    seed(a,1000,seed=42);seed(b,1000,seed=12345)
    assert a.execute('SELECT reading FROM readings WHERE row_id=1').fetchone()[0] != b.execute('SELECT reading FROM readings WHERE row_id=1').fetchone()[0]
    assert quality_results(a)['total']==quality_results(b)['total']==1000


def test_new_seed_is_reproducible():
    a=sqlite3.connect(':memory:');a.row_factory=sqlite3.Row
    b=sqlite3.connect(':memory:');b.row_factory=sqlite3.Row
    initialize(a);initialize(b)
    seed(a,1000,seed=12345);seed(b,1000,seed=12345)
    assert quality_results(a)==quality_results(b)
