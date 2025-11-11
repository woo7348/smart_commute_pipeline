import pandas as pd

# CSV 불러오기
df = pd.read_csv("output/od_monthly_202504_processed.csv")

# 출발지 기준 (dptre_emd_nm) 고유 동 수
unique_depart_emd = df["dptre_emd_nm"].nunique()

# 도착지 기준 (arvl_emd_nm) 고유 동 수
unique_arrival_emd = df["arvl_emd_nm"].nunique()

print(f"출발지 동 종류수: {unique_depart_emd}")
print(f"도착지 동 종류수: {unique_arrival_emd}")

# 만약 전체(출발 + 도착) 합쳐서 고유 동 수를 알고 싶다면
all_unique_emd = pd.concat([df["dptre_emd_nm"], df["arvl_emd_nm"]]).nunique()
print(f"전체 고유 동 종류수: {all_unique_emd}")

sorted(df["dptre_emd_nm"].dropna().unique())[:36]
sorted(df["arvl_emd_nm"].dropna().unique())[:36]

print(f"출발지 상위 36개 동:\n{df['dptre_emd_nm'].value_counts().head(36)}")
print(f"도착지 상위 36개 동:\n{df['arvl_emd_nm'].value_counts().head(36)}")