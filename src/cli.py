import argparse
from pathlib import Path
from .core import connect, initialize, seed, export_report, export_flagged_csv

def main():
    parser=argparse.ArgumentParser(description='Industrial data quality monitoring')
    parser.add_argument('--rows',type=int,default=12000)
    parser.add_argument('--db',default='data/telemetry.db')
    args=parser.parse_args()
    if args.rows < 1: parser.error('--rows must be positive')
    db_path=Path(args.db);db_path.parent.mkdir(parents=True,exist_ok=True)
    with connect(db_path) as db:
        initialize(db);seed(db,args.rows)
        report=export_report(db,'output/quality_report.json')
        export_flagged_csv(db,'output/flagged_readings.csv')
    print(f"Checked {report['total']:,} readings | Valid {report['valid']:,} | Invalid {report['invalid']:,} | Score {report['score']}%")
    print('Reports saved in output/')
if __name__=='__main__': main()
