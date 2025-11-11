import os
import json
import pandas as pd

RAW_DIR = "raw"
OUTPUT_DIR = "output"

def transform_od_bus_rail(opr_ym="202504"):
    # ✅ fetch 단계에서 생성된 한 달치 파일
    input_path = os.path.join(RAW_DIR, f"od_{opr_ym}_all.json")
    output_path = os.path.join(OUTPUT_DIR, f"od_monthly_{opr_ym}_processed.csv")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"❌ Input file not found: {input_path}")

    print(f"📂 Loading data from {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Unexpected JSON structure: {type(data)}")

    df = pd.DataFrame(data)

    # ✅ opr_ymd 존재 시 opr_ym (YYYYMM) 파생 컬럼 생성 (선택적)
    if "opr_ymd" in df.columns and "opr_ym" not in df.columns:
        df["opr_ym"] = df["opr_ymd"].astype(str).str[:6]

    # ✅ 필요한 컬럼만 선별 (opr_ymd 중심 유지)
    expected_cols = [
        "opr_ymd", "opr_ym", "dow_nm",
        "dptre_ctpv_nm", "dptre_sgg_nm", "dptre_emd_nm",
        "arvl_ctpv_nm", "arvl_sgg_nm", "arvl_emd_nm",
        "trfvlm", "pasg_hr_sum", "pasg_dstnc_sum"
    ]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]

    # ✅ 숫자형 컬럼 변환
    for col in ["trfvlm", "pasg_hr_sum", "pasg_dstnc_sum"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # ✅ 폴더 생성 후 CSV 저장
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"✅ Transformed and saved to {output_path}")
    print(f"📊 {len(df)} records processed")

if __name__ == "__main__":
    transform_od_bus_rail()
