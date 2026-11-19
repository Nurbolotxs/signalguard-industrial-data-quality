# Interactive Streamlit dashboard for industrial sensor data quality.
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from src.core import connect, initialize, seed, quality_results, trend, plant_summary, flagged_rows

st.set_page_config(page_title='SignalGuard | Data Quality',page_icon='📡',layout='wide')
st.markdown('''<style>
.stApp {background: #0b1120;color:#e5edf8}
.block-container {padding-top:2rem;max-width:1450px}
[data-testid="stMetric"] {background:linear-gradient(130deg,#17253b,#111c30);border:1px solid #2a3c56;border-radius:14px;padding:18px}
[data-testid="stMetricValue"] {color:#e8f3ff}
h1,h2,h3 {letter-spacing:-.025em}
</style>''',unsafe_allow_html=True)

def get_db():
    # Use a writable temporary directory on Streamlit Community Cloud.
    # Local runs keep the database inside the project directory.
    import os
    import tempfile
    path = Path(tempfile.gettempdir()) / 'signalguard' / 'telemetry.db'
    path.parent.mkdir(parents=True, exist_ok=True)
    db=connect(path)
    # If the user has run CLI, use the existing data without destroying it.
    if not db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='readings'").fetchone():
        initialize(db);seed(db)
    return db

# A button callback runs before the dashboard script on each interaction.
# Use an independent SQLite connection and close it before Streamlit reruns.
def regenerate_dataset():
    connection = get_db()
    try:
        initialize(connection)
        seed(connection)
    finally:
        connection.close()

# Open a fresh connection for each Streamlit script execution.
# SQLite connections must not be reused across Streamlit worker threads.
db=get_db()
st.caption('SIGNALGUARD  /  INDUSTRIAL ANALYTICS  /  DEMO DATA')
st.title('📡 Industrial Data Quality Monitor')
st.write('Automated validation of industrial telemetry with SQL-powered checks, transparent rule counts, and interactive diagnostics.')
with st.sidebar:
    st.header('Control center')
    st.success('● Monitoring ready')
    st.caption('Synthetic telemetry • 30 sensors • 3 plants')
    st.button('Regenerate demo dataset', width='stretch', on_click=regenerate_dataset)
    st.divider()
    st.markdown('**Validation rules**')
    st.caption('Missing reading · Out-of-range · Unknown sensor · Duplicate event · Future timestamp')
    st.caption('Threshold: 0–120 units; reference date: 2026-11-19')

r=quality_results(db)
a,b,c,d=st.columns(4)
a.metric('Records inspected',f"{r['total']:,}")
b.metric('Valid readings',f"{r['valid']:,}")
c.metric('Flagged readings',f"{r['invalid']:,}")
d.metric('Quality score',f"{r['score']:.2f}%")
st.caption('A reading may violate multiple rules. Invalid readings are counted once in the headline metric.')
left,right=st.columns([1.15,1])
with left:
    st.subheader('Rule violations')
    rules=pd.DataFrame([{'Rule':k.replace('_',' ').title(),'Flagged':v} for k,v in r['rules'].items()])
    fig=px.bar(rules,x='Flagged',y='Rule',orientation='h',color='Flagged',color_continuous_scale=['#19b6bd','#f59e69'])
    fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',coloraxis_showscale=False,height=360,margin=dict(l=0,r=12,t=10,b=0),yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig,width='stretch')
with right:
    st.subheader('Pass / fail distribution')
    df=pd.DataFrame([{'Status':'Valid','Count':r['valid']},{'Status':'Flagged','Count':r['invalid']}])
    fig=px.pie(df,names='Status',values='Count',hole=.68,color='Status',color_discrete_map={'Valid':'#22c5a1','Flagged':'#fb7185'})
    fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',height=360,margin=dict(l=0,r=0,t=10,b=0),legend=dict(orientation='h',y=-.05))
    st.plotly_chart(fig,width='stretch')

st.subheader('Daily data quality trend')
t=pd.DataFrame(trend(db))
if not t.empty:
    t['quality_pct']=((t['total']-t['invalid'])/t['total']*100).round(2)
    fig=px.line(t,x='day',y='quality_pct',markers=True,labels={'day':'Date','quality_pct':'Quality (%)'})
    fig.update_traces(line_color='#38bdf8',line_width=3)
    fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',height=300,margin=dict(l=0,r=15,t=10,b=0),yaxis_range=[0,101])
    st.plotly_chart(fig,width='stretch')

st.subheader('Plant breakdown')
plants=pd.DataFrame(plant_summary(db))
if not plants.empty:
    plants['quality_pct']=((plants['total']-plants['invalid'])/plants['total']*100).round(2)
    st.dataframe(plants.rename(columns={'plant':'Plant','total':'Readings','invalid':'Flagged','quality_pct':'Quality (%)'}),hide_index=True,width='stretch')

st.subheader('Flagged records explorer')
rows=pd.DataFrame(flagged_rows(db,2000))
if not rows.empty:
    sensor_filter=st.multiselect('Sensor ID',sorted(rows['sensor_id'].unique().tolist()),placeholder='All sensors')
    if sensor_filter: rows=rows[rows['sensor_id'].isin(sensor_filter)]
    st.dataframe(rows,hide_index=True,width='stretch',height=300)
    st.download_button('⬇ Download filtered flagged records',rows.to_csv(index=False).encode(),file_name='flagged_readings.csv',mime='text/csv')
else: st.info('No violations found.')
st.caption('Portfolio demonstration • Synthetic data only • SQL and Python validation • Streamlit + Plotly')

# Explicitly release the per-run SQLite connection.
db.close()
