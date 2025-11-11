# SmartCommute Data Pipeline 🚍🌦

## 🎯 목표
날씨 및 버스 도착정보를 수집해 출근시간 연관성을 분석하는 파이프라인 구축.

## 👥 역할 분담
| 역할 | 담당자 | 주요 업무 |
|------|---------|-----------|
| Engineer A | Data Ingestion | API 데이터 수집, 전처리, 로그 관리 |
| Engineer B | DB & Automation | PostgreSQL 스키마 설계, Airflow 자동화 |

## ⚙️ 실행 순서
```bash
# 1. 환경 변수 설정
cp .env.example .env

# 2. 도커 환경 시작
docker compose up -d

# 3. 수동 테스트 (Airflow DAG 없이)
python src/fetch_weather.py
python src/fetch_bus.py
python src/transform_merge.py
python src/load_to_db.py

# 4. Airflow Web UI 접속
http://localhost:8081
