"""Generate figures for the report."""
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['font.family']='DejaVu Sans'
mpl.rcParams['axes.spines.top']=False
mpl.rcParams['axes.spines.right']=False
mpl.rcParams['axes.edgecolor']='#5e6678'
mpl.rcParams['axes.labelcolor']='#0b1d3a'
mpl.rcParams['xtick.color']='#5e6678'
mpl.rcParams['ytick.color']='#5e6678'
mpl.rcParams['figure.dpi']=160

NAVY='#0b1d3a'; SKY='#4ea7ce'; SKY_LITE='#7fc5e3'; GOLD='#e2b770'; CORAL='#ee7d6a'; BONE='#fbf8f3'

SRC='/home/mocap/toospoint/Voyce data Jan - Apr JEWISH MEMORIAL.xlsx'
OUTDIR='/home/mocap/toospoint/reports/figures/'

df=pd.read_excel(SRC)
df['Request Time (Eastern Standard Time)']=pd.to_datetime(df['Request Time (Eastern Standard Time)'])
fr=df[df['Source Language'].astype(str).str.strip().str.lower()=='french'].copy()
fr_serv=fr[fr['Status']=='Serviced'].copy()
fr_canx=fr[fr['Status']=='Cancelled'].copy()

# === FIG 1: Cancellation rate, English vs French ===
fig, ax = plt.subplots(figsize=(7,3.6))
labels=['English-source','French-source']
en_cx=(df[df['Source Language']=='English']['Status']=='Cancelled').mean()
fr_cx=(fr['Status']=='Cancelled').mean()
vals=[en_cx, fr_cx]
bars=ax.bar(labels, vals, color=[SKY, CORAL], width=0.55, edgecolor='white', linewidth=2)
ax.set_ylabel('Cancellation rate')
ax.set_ylim(0,1)
ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
for b,v in zip(bars,vals):
    ax.text(b.get_x()+b.get_width()/2, v+0.02, f'{v:.1%}', ha='center', va='bottom',
            fontsize=12, fontweight='bold', color=NAVY)
ax.set_title('French calls are abandoned 4.8× more often than English',
             fontsize=12, color=NAVY, pad=12, loc='left', fontweight='bold')
ax.grid(axis='y', linestyle=':', color='#cccccc', alpha=0.6)
plt.tight_layout()
plt.savefig(OUTDIR+'fig1_cancellation_compare.pdf', bbox_inches='tight')
plt.savefig(OUTDIR+'fig1_cancellation_compare.png', bbox_inches='tight')
plt.close()

# === FIG 2: Cancellation rate per French→target ===
gp=fr.groupby('Target Language').agg(
    total=('Id','count'),
    cancelled=('Status', lambda s:(s=='Cancelled').sum()),
)
gp['rate']=gp['cancelled']/gp['total']
gp=gp.sort_values('rate', ascending=True)
fig, ax = plt.subplots(figsize=(7,3.6))
bars=ax.barh(gp.index, gp['rate'], color=SKY, edgecolor='white', linewidth=2)
ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
ax.set_xlim(0,1)
for i,(b,r,total) in enumerate(zip(bars, gp['rate'], gp['total'])):
    ax.text(r+0.02, b.get_y()+b.get_height()/2, f'{r:.0%}  ({int(total)} calls)',
            va='center', fontsize=10, color=NAVY)
ax.set_xlabel('Cancellation rate')
ax.set_title('French→Spanish cancellations dominate the unmet demand',
             fontsize=12, color=NAVY, pad=12, loc='left', fontweight='bold')
ax.grid(axis='x', linestyle=':', color='#cccccc', alpha=0.6)
plt.tight_layout()
plt.savefig(OUTDIR+'fig2_cancellation_by_pair.pdf', bbox_inches='tight')
plt.savefig(OUTDIR+'fig2_cancellation_by_pair.png', bbox_inches='tight')
plt.close()

# === FIG 3: Serviced vs True (annualized minutes per pair) ===
avg=fr_serv.groupby('Target Language')['Service Minutes'].mean()
unmet=fr_canx.groupby('Target Language')['Id'].count()*avg
serv=fr_serv.groupby('Target Language')['Service Minutes'].sum()
df_dem=pd.DataFrame({'Serviced':serv*3, 'Unmet (cancelled)':unmet*3}).fillna(0)
df_dem=df_dem.sort_values('Serviced', ascending=True)
fig, ax = plt.subplots(figsize=(7,3.6))
df_dem.plot(kind='barh', stacked=True, ax=ax,
            color=[SKY, CORAL], edgecolor='white', linewidth=2, width=0.7)
totals=df_dem.sum(axis=1)
for i,t in enumerate(totals):
    ax.text(t+150, i, f'{int(t):,} min/yr', va='center', fontsize=10, color=NAVY, fontweight='bold')
ax.set_xlabel('Annualized minutes')
ax.set_title('True demand is 3–13× larger than what was served',
             fontsize=12, color=NAVY, pad=12, loc='left', fontweight='bold')
ax.legend(loc='lower right', frameon=False)
ax.grid(axis='x', linestyle=':', color='#cccccc', alpha=0.6)
ax.set_xlim(0, totals.max()*1.18)
plt.tight_layout()
plt.savefig(OUTDIR+'fig3_true_vs_serviced.pdf', bbox_inches='tight')
plt.savefig(OUTDIR+'fig3_true_vs_serviced.png', bbox_inches='tight')
plt.close()

# === FIG 4: Hour-of-day demand vs cancellation ===
fr['hour']=fr['Request Time (Eastern Standard Time)'].dt.hour
hr=fr.groupby('hour').agg(
    total=('Id','count'),
    cancelled=('Status', lambda s:(s=='Cancelled').sum()),
)
hr['serviced']=hr['total']-hr['cancelled']
hr=hr.reindex(range(7,19), fill_value=0)
fig, ax = plt.subplots(figsize=(7,3.6))
x=np.arange(len(hr))
ax.bar(x, hr['serviced'], color=SKY, label='Serviced', edgecolor='white', linewidth=1.5)
ax.bar(x, hr['cancelled'], bottom=hr['serviced'], color=CORAL, label='Cancelled', edgecolor='white', linewidth=1.5)
ax.set_xticks(x)
ax.set_xticklabels([f'{h}:00' for h in hr.index], rotation=0)
ax.set_ylabel('French-source calls (count)')
ax.set_title('Demand peaks 9 AM – 2 PM; cancellations rise late afternoon',
             fontsize=12, color=NAVY, pad=12, loc='left', fontweight='bold')
ax.legend(loc='upper right', frameon=False)
ax.grid(axis='y', linestyle=':', color='#cccccc', alpha=0.6)
plt.tight_layout()
plt.savefig(OUTDIR+'fig4_hourly.pdf', bbox_inches='tight')
plt.savefig(OUTDIR+'fig4_hourly.png', bbox_inches='tight')
plt.close()

# === FIG 5: Pool vs need (gap) ===
PAIRS=['Spanish','Punjabi','Arabic','Haitian Creole']
POOL={'Spanish':19,'Punjabi':1,'Arabic':7,'Haitian Creole':64}
need=[]
for p in PAIRS:
    avg_p = fr_serv[fr_serv['Target Language']==p]['Service Minutes'].mean()
    cx_n  = (fr_canx['Target Language']==p).sum()
    serv_p = fr_serv[fr_serv['Target Language']==p]['Service Minutes'].sum()
    truem  = (serv_p + cx_n*avg_p)*3/12
    need.append(int(np.ceil(truem/6400)))
pool=[POOL[p] for p in PAIRS]

fig, ax = plt.subplots(figsize=(7,3.6))
x=np.arange(len(PAIRS))
w=0.35
b1=ax.bar(x-w/2, need, w, color=CORAL, label='Interpreters needed (true demand)', edgecolor='white', linewidth=1.5)
b2=ax.bar(x+w/2, pool, w, color=SKY,   label='Current French pool', edgecolor='white', linewidth=1.5)
ax.set_xticks(x); ax.set_xticklabels([f'French→{p}' for p in PAIRS])
ax.set_ylabel('Interpreters')
ax.set_title('Pool sizing vs true demand — Spanish & Punjabi appear under-served',
             fontsize=12, color=NAVY, pad=12, loc='left', fontweight='bold')
ax.legend(loc='upper right', frameon=False)
ax.grid(axis='y', linestyle=':', color='#cccccc', alpha=0.6)
for bars,values in [(b1,need),(b2,pool)]:
    for b,v in zip(bars,values):
        ax.text(b.get_x()+b.get_width()/2, v+0.5, str(v), ha='center', va='bottom',
                fontsize=10, color=NAVY, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTDIR+'fig5_pool_vs_need.pdf', bbox_inches='tight')
plt.savefig(OUTDIR+'fig5_pool_vs_need.png', bbox_inches='tight')
plt.close()

print('Figures written to', OUTDIR)
