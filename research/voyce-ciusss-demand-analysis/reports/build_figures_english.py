"""Generate figures for the English-source report."""
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

NAVY='#0b1d3a'; SKY='#4ea7ce'; SKY_LITE='#7fc5e3'; GOLD='#e2b770'; CORAL='#ee7d6a'

SRC='/home/mocap/toospoint/Voyce data Jan - Apr JEWISH MEMORIAL.xlsx'
OUTDIR='/home/mocap/toospoint/reports/figures_en/'

df=pd.read_excel(SRC)
df['Request Time (Eastern Standard Time)']=pd.to_datetime(df['Request Time (Eastern Standard Time)'])
en=df[df['Source Language'].astype(str).str.strip().str.lower()=='english'].copy()
en_serv=en[en['Status']=='Serviced'].copy()
en_canx=en[en['Status']=='Cancelled'].copy()

# === FIG 1: Top 15 target languages by serviced minutes ===
g = en_serv.groupby('Target Language')['Service Minutes'].sum().sort_values(ascending=True).tail(15)
fig, ax = plt.subplots(figsize=(7,5.0))
bars = ax.barh(g.index, g.values, color=SKY, edgecolor='white', linewidth=2)
for b,v in zip(bars, g.values):
    ax.text(v+v.max()*0.01 if False else v+max(g.values)*0.01, b.get_y()+b.get_height()/2,
            f'{int(v):,}', va='center', fontsize=9, color=NAVY)
ax.set_xlabel('Serviced minutes (Jan–Apr 2025)')
ax.set_title('Top-15 English target languages by serviced volume',
             fontsize=12, color=NAVY, pad=12, loc='left', fontweight='bold')
ax.grid(axis='x', linestyle=':', color='#cccccc', alpha=0.6)
ax.set_xlim(0, max(g.values)*1.14)
plt.tight_layout()
plt.savefig(OUTDIR+'fig1_top_targets.pdf', bbox_inches='tight')
plt.savefig(OUTDIR+'fig1_top_targets.png', bbox_inches='tight')
plt.close()

# === FIG 2: Cancellation rate — overall vs problem languages ===
gp = en.groupby('Target Language').agg(
    total=('Id','count'),
    cancelled=('Status', lambda s:(s=='Cancelled').sum()),
)
gp['rate']=gp['cancelled']/gp['total']
# Languages with > 30 calls (significant volume) AND highest cancellation rates, top 12
problem = gp[gp['total']>=30].sort_values('rate', ascending=False).head(12).sort_values('rate', ascending=True)
fig, ax = plt.subplots(figsize=(7,4.5))
overall = (en['Status']=='Cancelled').mean()
colors = [CORAL if r>overall*1.3 else SKY for r in problem['rate']]
bars=ax.barh(problem.index, problem['rate'], color=colors, edgecolor='white', linewidth=2)
ax.axvline(overall, color=NAVY, linestyle='--', linewidth=1.2, alpha=0.6)
ax.text(overall+0.005, len(problem)-0.4, f'Avg: {overall:.1%}', color=NAVY, fontsize=9, fontweight='bold')
ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
for b,r,t in zip(bars, problem['rate'], problem['total']):
    ax.text(r+0.005, b.get_y()+b.get_height()/2, f'{r:.0%} ({int(t)})',
            va='center', fontsize=9, color=NAVY)
ax.set_xlabel('Cancellation rate (target languages with ≥30 calls)')
ax.set_title('Cancellation outliers vs.\xa015.9% English-source baseline',
             fontsize=12, color=NAVY, pad=12, loc='left', fontweight='bold')
ax.grid(axis='x', linestyle=':', color='#cccccc', alpha=0.6)
ax.set_xlim(0, max(problem['rate'])*1.20)
plt.tight_layout()
plt.savefig(OUTDIR+'fig2_cancellation_outliers.pdf', bbox_inches='tight')
plt.savefig(OUTDIR+'fig2_cancellation_outliers.png', bbox_inches='tight')
plt.close()

# === FIG 3: Stacked - top 10 pairs - serviced vs unmet (annualized) ===
avg=en_serv.groupby('Target Language')['Service Minutes'].mean()
unmet=en_canx.groupby('Target Language')['Id'].count()*avg
serv=en_serv.groupby('Target Language')['Service Minutes'].sum()
df_dem=pd.DataFrame({'Serviced':serv*3, 'Unmet (cancelled)':unmet*3}).fillna(0)
df_dem['total']=df_dem.sum(axis=1)
df_dem=df_dem.sort_values('total', ascending=False).head(10).drop(columns='total').sort_values('Serviced', ascending=True)
fig, ax = plt.subplots(figsize=(7,4.4))
df_dem.plot(kind='barh', stacked=True, ax=ax,
            color=[SKY, CORAL], edgecolor='white', linewidth=2, width=0.7)
totals=df_dem.sum(axis=1)
for i,t in enumerate(totals):
    ax.text(t+totals.max()*0.01, i, f'{int(t):,}',
            va='center', fontsize=9, color=NAVY, fontweight='bold')
ax.set_xlabel('Annualized minutes')
ax.set_title('Top-10 English pairs — serviced vs unmet (annualized)',
             fontsize=12, color=NAVY, pad=12, loc='left', fontweight='bold')
ax.legend(loc='lower right', frameon=False)
ax.grid(axis='x', linestyle=':', color='#cccccc', alpha=0.6)
ax.set_xlim(0, totals.max()*1.18)
plt.tight_layout()
plt.savefig(OUTDIR+'fig3_top10_serviced_vs_unmet.pdf', bbox_inches='tight')
plt.savefig(OUTDIR+'fig3_top10_serviced_vs_unmet.png', bbox_inches='tight')
plt.close()

# === FIG 4: Hourly distribution ===
en['hour']=en['Request Time (Eastern Standard Time)'].dt.hour
hr=en.groupby('hour').agg(
    total=('Id','count'),
    cancelled=('Status', lambda s:(s=='Cancelled').sum()),
)
hr['serviced']=hr['total']-hr['cancelled']
hr=hr.reindex(range(0,24), fill_value=0)
hr=hr.loc[(hr['total']>0)]
fig, ax = plt.subplots(figsize=(7,3.6))
x=np.arange(len(hr))
ax.bar(x, hr['serviced'], color=SKY, label='Serviced', edgecolor='white', linewidth=1.2)
ax.bar(x, hr['cancelled'], bottom=hr['serviced'], color=CORAL, label='Cancelled', edgecolor='white', linewidth=1.2)
ax.set_xticks(x); ax.set_xticklabels([f'{h:02d}:00' for h in hr.index], rotation=45, fontsize=8)
ax.set_ylabel('English-source calls (count)')
ax.set_title('Demand peaks 9{:}00–14{:}00 EST; long tail into late afternoon'.replace('{:}', ':'),
             fontsize=12, color=NAVY, pad=12, loc='left', fontweight='bold')
ax.legend(loc='upper right', frameon=False)
ax.grid(axis='y', linestyle=':', color='#cccccc', alpha=0.6)
plt.tight_layout()
plt.savefig(OUTDIR+'fig4_hourly.pdf', bbox_inches='tight')
plt.savefig(OUTDIR+'fig4_hourly.png', bbox_inches='tight')
plt.close()

# === FIG 5: Long-tail breakdown — % of total volume covered by top-N pairs ===
serv_sorted = en_serv.groupby('Target Language')['Service Minutes'].sum().sort_values(ascending=False)
total = serv_sorted.sum()
cum = serv_sorted.cumsum()/total
fig, ax = plt.subplots(figsize=(7,3.8))
ax.plot(range(1,len(cum)+1), cum.values, color=NAVY, linewidth=2.2)
ax.fill_between(range(1,len(cum)+1), cum.values, alpha=0.10, color=SKY)
# Annotate the 80%, 90%, 95% reach
for tgt in [0.8, 0.9, 0.95]:
    n = (cum<=tgt).sum()+1
    ax.scatter([n], [cum.iloc[n-1]], s=44, color=CORAL, zorder=3)
    ax.annotate(f'  {n} languages cover {tgt:.0%}',
                xy=(n, cum.iloc[n-1]), xytext=(8, -2), textcoords='offset points',
                fontsize=9, color=NAVY)
ax.set_xlabel('Number of target languages (ranked by volume)')
ax.set_ylabel('Cumulative share of serviced minutes')
ax.set_xlim(1, len(cum))
ax.set_ylim(0, 1.02)
ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
ax.set_title('A handful of languages cover most of the load',
             fontsize=12, color=NAVY, pad=12, loc='left', fontweight='bold')
ax.grid(axis='y', linestyle=':', color='#cccccc', alpha=0.6)
plt.tight_layout()
plt.savefig(OUTDIR+'fig5_long_tail.pdf', bbox_inches='tight')
plt.savefig(OUTDIR+'fig5_long_tail.png', bbox_inches='tight')
plt.close()

print('English figures written to', OUTDIR)
