# Airflow Configuration Guide

## 🎯 목표
Airflow를 통해 데이터 파이프라인을 자동화하고 모니터링하기.

## 📁 파일 구조
```
dags/
├── smart_commute_weather_dag.py          # 날씨 데이터 파이프라인
├── smart_commute_bus_seoul_pipeline_dag.py  # 서울 버스 데이터 파이프라인
├── smart_commute_unified_dag.py          # 통합 데이터 파이프라인 (권장)
├── smart_commute_dag.py                  # [레거시] 기존 DAG (deprecated)
└── smart_commute_bus_seoul_dag.py        # [레거시] 기존 버스 DAG (deprecated)

src/
├── fetch_weather.py                  # 기상청 API에서 날씨 데이터 수집
├── fetch_bus_seoul.py                # 서울 버스 API에서 버스 정보 수집
├── transform_weather.py              # 날씨 데이터 전처리
├── transform_bus_seoul.py            # 버스 데이터 전처리
├── transform_merge.py                # 날씨 + 버스 데이터 통합
└── load_to_db.py                     # PostgreSQL에 데이터 적재

docker-compose.yaml                   # Airflow + PostgreSQL 환경 설정
requirements.txt                      # Python 패키지 의존성
```

---

## 🚀 시작하기

### 1️⃣ Docker Compose 시작
```bash
# 컨테이너 시작 (초기화 포함)
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f airflow
```

### 2️⃣ Airflow 웹 UI 접속
- URL: http://localhost:8081
- 기본 로그인: `admin` / `admin`

### 3️⃣ PostgreSQL 접속 (Adminer)
- URL: http://localhost:8082
- 서버: `postgres`
- 사용자: `airflow`
- 비밀번호: `airflow`
- DB: `airflow`

---

## ⚙️ Airflow 설정 (Connections & Variables)

### 📌 PostgreSQL Connection 설정

**UI를 통한 설정 (권장)**
1. Airflow 웹 UI → Admin → Connections
2. "+" 버튼 클릭
3. 다음 정보 입력:
   - **Conn Id**: `smartcommute_db`
   - **Conn Type**: `Postgres`
   - **Host**: `postgres` (Docker 내부 네트워크)
   - **Schema**: `airflow`
   - **Login**: `airflow`
   - **Password**: `airflow`
   - **Port**: `5432`
4. "Save" 클릭

**CLI를 통한 설정**
```bash
docker-compose exec airflow airflow connections add smartcommute_db \
  --conn-type postgres \
  --conn-host postgres \
  --conn-login airflow \
  --conn-password airflow \
  --conn-port 5432 \
  --conn-schema airflow
```

### 📌 Airflow Variables 설정

**UI를 통한 설정 (권장)**
1. Airflow 웹 UI → Admin → Variables
2. "+" 버튼 클릭해서 아래 변수들 추가:

| Variable Name | Value | Description |
|---|---|---|
| `data_directory` | `/opt/airflow/data` | 데이터 저장 디렉토리 |
| `raw_data_dir` | `/opt/airflow/raw` | 원본 데이터 디렉토리 |
| `output_data_dir` | `/opt/airflow/output` | 처리된 데이터 디렉토리 |
| `weather_api_key` | `[your-api-key]` | 기상청 API 키 (.env에서 복사) |
| `bus_api_key` | `[your-api-key]` | 서울 버스 API 키 (.env에서 복사) |
| `db_host` | `postgres` | DB 호스트 |
| `db_name` | `airflow` | DB 이름 |
| `db_user` | `airflow` | DB 사용자 |
| `db_port` | `5432` | DB 포트 |

**CLI를 통한 설정**
```bash
docker-compose exec airflow airflow variables set data_directory /opt/airflow/data
docker-compose exec airflow airflow variables set weather_api_key your_api_key_here
```

### 📌 환경변수로 설정 (docker-compose.yaml 수정)

`docker-compose.yaml`의 `airflow` 서비스 `environment` 섹션에 추가:
```yaml
environment:
  - AIRFLOW_VAR_DATA_DIRECTORY=/opt/airflow/data
  - AIRFLOW_VAR_WEATHER_API_KEY=${WEATHER_API_KEY}
  - AIRFLOW_VAR_BUS_API_KEY=${BUS_API_KEY}
  - AIRFLOW_CONN_SMARTCOMMUTE_DB=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
```

---

## 📊 DAG 소개

### 🌤️ smart_commute_weather_dag
**목적**: 기상청에서 날씨 데이터를 수집하고 DB에 적재
- **스케줄**: 매 3시간마다 (06:00~22:00)
- **태스크**:
  1. `fetch_weather` - 기상청 API 호출
  2. `transform_weather` - 데이터 정제
  3. `load_weather_to_db` - PostgreSQL 적재

**수동 실행**:
```bash
docker-compose exec airflow airflow dags test smart_commute_weather_pipeline 2025-11-11
```

---

### 🚌 smart_commute_bus_seoul_pipeline_dag
**목적**: 서울 버스 도착정보를 수집하고 DB에 적재
- **스케줄**: 평일 06:00~10:00, 매 15분마다
- **태스크**:
  1. `fetch_bus_seoul` - 서울 버스 API 호출
  2. `transform_bus_seoul` - 데이터 정제
  3. `load_bus_seoul` - PostgreSQL 적재

**수동 실행**:
```bash
docker-compose exec airflow airflow dags test smart_commute_bus_seoul_pipeline 2025-11-11
```

---

### 🔗 smart_commute_unified_dag (권장)
**목적**: 날씨 + 버스 데이터를 통합하여 분석
- **스케줄**: 매일 11:00 AM (출근시간대 이후)
- **구조**:
  ```
  fetch_weather ─┐
                  ├─→ transform_weather ─┐
  fetch_bus ─────┤                       ├─→ merge_data ─→ load_to_db
                  ├─→ transform_bus ──────┘
  ```
- **주요 기능**: 병렬 처리로 효율성 증대, 에러 재시도, 상세 로깅

**수동 실행**:
```bash
docker-compose exec airflow airflow dags test smart_commute_unified_pipeline 2025-11-11
```

---

## 🛠️ 유용한 Airflow CLI 명령어

```bash
# DAG 목록 확인
docker-compose exec airflow airflow dags list

# 특정 DAG 정보
docker-compose exec airflow airflow dags info smart_commute_weather_pipeline

# DAG 테스트 실행
docker-compose exec airflow airflow dags test <DAG_ID> <DATE>

# 특정 태스크 테스트
docker-compose exec airflow airflow tasks test <DAG_ID> <TASK_ID> <DATE>

# DAG 활성화/비활성화
docker-compose exec airflow airflow dags pause <DAG_ID>
docker-compose exec airflow airflow dags unpause <DAG_ID>

# 변수 확인
docker-compose exec airflow airflow variables list

# Connection 확인
docker-compose exec airflow airflow connections list
```

---

## 📝 .env 파일 설정

`.env.example`을 참고해서 `.env` 파일 생성:

```bash
# Database
DB_HOST=postgres
DB_NAME=airflow
DB_USER=airflow
DB_PASS=airflow
DB_PORT=5432

# APIs
WEATHER_API_KEY=your_weather_api_key
BUS_SEOUL_API_KEY=your_bus_api_key

# Airflow
AIRFLOW__CORE__FERNET_KEY=9c4guElT4vaK0Q-Rjs1E3Lf4cUgeRKLEAF7LJJwY0Nw=
```

---

## 🐛 문제 해결

### Airflow가 시작되지 않음
```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f airflow

# 재시작
docker-compose restart airflow
```

### DAG가 표시되지 않음
```bash
# 컨테이너 내에서 dags 폴더 확인
docker-compose exec airflow ls -la /opt/airflow/dags/

# DAG 구문 검사
docker-compose exec airflow python -m py_compile /opt/airflow/dags/your_dag.py
```

### 데이터베이스 연결 오류
```bash
# PostgreSQL 접근성 확인
docker-compose exec postgres psql -U airflow -d airflow -c "SELECT 1;"

# Connection 테스트
docker-compose exec airflow airflow connections test smartcommute_db
```

---

## 📚 참고 자료
- [Apache Airflow 공식 문서](https://airflow.apache.org)
- [Airflow Operators](https://airflow.apache.org/docs/apache-airflow/stable/operators.html)
- [DAG 작성 가이드](https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html)

---

## ✅ 체크리스트

- [ ] Docker Compose로 Airflow 시작
- [ ] 웹 UI (localhost:8081)에서 로그인
- [ ] PostgreSQL Connection 설정
- [ ] Airflow Variables 설정
- [ ] DAG가 UI에 표시되는지 확인
- [ ] 수동으로 DAG 실행해보기
- [ ] 로그 확인 및 성공 여부 검증
- [ ] 스케줄 설정 및 자동 실행 확인
