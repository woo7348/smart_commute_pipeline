# DAG 테스트 가이드

## 🧪 로컬에서 DAG 테스트

### 1️⃣ DAG 구문 검증

**Python 구문 검사**:
```bash
python -m py_compile dags/smart_commute_weather_dag.py
python -m py_compile dags/smart_commute_bus_seoul_pipeline_dag.py
python -m py_compile dags/smart_commute_unified_dag.py
```

**제공된 검증 스크립트 사용**:
```bash
python scripts/validate_dags.py
```

예상 출력:
```
🔍 5개의 DAG 파일 검증 중...

✅ smart_commute_weather_dag.py
   - DAG: smart_commute_weather_pipeline

✅ smart_commute_bus_seoul_pipeline_dag.py
   - DAG: smart_commute_bus_seoul_pipeline

✅ smart_commute_unified_dag.py
   - DAG: smart_commute_unified_pipeline

...

✅ 모든 DAG이 유효합니다! (총 3개 DAG)
```

---

## 🐳 Docker에서 DAG 테스트

### 1️⃣ Airflow 컨테이너 시작

```bash
docker-compose up -d
```

상태 확인:
```bash
docker-compose ps
```

### 2️⃣ DAG 목록 확인

```bash
docker-compose exec airflow airflow dags list
```

예상 출력:
```
dag_id                              | owner         | ... | status
====================================================================
smart_commute_pipeline              | smartcommute  | ... | 
smart_commute_bus_seoul_pipeline    | smartcommute  | ... | 
smart_commute_unified_pipeline      | smartcommute  | ... | 
...
```

### 3️⃣ 특정 DAG 테스트

**DAG 전체 테스트 실행** (모든 태스크 실행):
```bash
docker-compose exec airflow airflow dags test smart_commute_weather_pipeline 2025-11-11
```

예상 출력:
```
[2025-11-11 15:30:00] Starting DAG: smart_commute_weather_pipeline
[2025-11-11 15:30:01] Running: fetch_weather
🚀 Executing: fetch_weather.py
✅ fetch_weather.py completed successfully
[2025-11-11 15:30:15] Task: fetch_weather completed in 14s
[2025-11-11 15:30:16] Running: transform_weather
...
```

**특정 태스크만 테스트**:
```bash
docker-compose exec airflow airflow tasks test smart_commute_weather_pipeline fetch_weather 2025-11-11
```

### 4️⃣ 태스크 로그 확인

```bash
docker-compose exec airflow airflow tasks logs smart_commute_weather_pipeline fetch_weather 2025-11-11
```

---

## 🔄 시뮬레이션: DAG 실행 흐름

### 날씨 데이터 파이프라인 테스트

```bash
# 1. DAG 테스트
docker-compose exec airflow airflow dags test smart_commute_weather_pipeline 2025-11-11

# 2. 각 태스크 로그 확인
docker-compose exec airflow airflow tasks logs smart_commute_weather_pipeline fetch_weather 2025-11-11
docker-compose exec airflow airflow tasks logs smart_commute_weather_pipeline transform_weather 2025-11-11
docker-compose exec airflow airflow tasks logs smart_commute_weather_pipeline load_weather_to_db 2025-11-11

# 3. DB에 데이터가 적재되었는지 확인
docker-compose exec postgres psql -U airflow -d airflow -c "SELECT COUNT(*) FROM weather_data LIMIT 5;"
```

### 통합 파이프라인 테스트

```bash
# 1. DAG 테스트
docker-compose exec airflow airflow dags test smart_commute_unified_pipeline 2025-11-11

# 2. 각 단계별 로그 확인
docker-compose exec airflow airflow tasks logs smart_commute_unified_pipeline fetch_weather 2025-11-11
docker-compose exec airflow airflow tasks logs smart_commute_unified_pipeline transform_merge 2025-11-11
docker-compose exec airflow airflow tasks logs smart_commute_unified_pipeline load_to_db 2025-11-11

# 3. 웹 UI에서 DAG 그래프 시각화
# http://localhost:8081 → DAGs → smart_commute_unified_pipeline
```

---

## 📊 웹 UI에서 테스트

### 1️⃣ Airflow 웹 UI 접속
- URL: http://localhost:8081
- 로그인: `admin` / `admin`

### 2️⃣ DAG 활성화
1. DAGs 목록에서 DAG 찾기
2. 토글 버튼으로 활성화

### 3️⃣ 수동 실행
1. DAG 클릭
2. "Trigger DAG" 버튼 클릭
3. 또는 특정 날짜로 "Trigger DAG w/ config" 클릭

### 4️⃣ 태스크 모니터링
1. "Graph" 또는 "Tree" 탭에서 실행 상태 확인
2. 각 태스크 클릭 → 로그 확인

---

## ✅ 테스트 체크리스트

### 로컬 환경
- [ ] DAG 구문 검사 (validate_dags.py)
- [ ] 모든 import 오류 없음
- [ ] 필요 스크립트 파일 존재 확인

### Docker 환경
- [ ] `docker-compose up -d` 성공
- [ ] Airflow 웹 UI 접속 가능
- [ ] `airflow dags list`에 모든 DAG 표시
- [ ] PostgreSQL 연결 가능

### DAG 실행
- [ ] 각 DAG 수동 테스트 성공
- [ ] 모든 태스크 로그 확인 가능
- [ ] DB에 데이터 적재 확인

### 스케줄 실행
- [ ] DAG 활성화 후 스케줄 시간에 자동 실행
- [ ] 예상 시간에 웹 UI에 실행 기록 표시
- [ ] 실패 시 재시도 작동

---

## 🐛 일반적인 문제 해결

### 문제: "Module not found" 에러

**원인**: Python 경로 문제
**해결**:
```bash
# 컨테이너 내에서 경로 확인
docker-compose exec airflow ls -la /opt/airflow/src/

# 절대 경로 확인
docker-compose exec airflow python -c "import sys; print('\n'.join(sys.path))"
```

### 문제: "Connection refused" DB 에러

**원인**: PostgreSQL 연결 실패
**해결**:
```bash
# PostgreSQL 상태 확인
docker-compose exec postgres psql -U airflow -d airflow -c "SELECT 1;"

# Connection 테스트
docker-compose exec airflow airflow connections test smartcommute_db
```

### 문제: DAG이 보이지 않음

**원인**: DAG 파일 로드 실패
**해결**:
```bash
# DAG 디렉토리 확인
docker-compose exec airflow ls -la /opt/airflow/dags/

# Airflow 로그 확인
docker-compose logs -f airflow | grep -i "error\|failed"

# DAG 파일 구문 검사
docker-compose exec airflow python -m py_compile /opt/airflow/dags/your_dag.py
```

### 문제: 태스크 실패

**해결 단계**:
1. 웹 UI에서 실패한 태스크 클릭
2. "Logs" 탭에서 전체 에러 메시지 확인
3. 원본 스크립트 직접 실행:
   ```bash
   docker-compose exec airflow python /opt/airflow/src/fetch_weather.py
   ```

---

## 🚀 다음 단계

1. ✅ DAG 검증 및 테스트 완료
2. ⏭️ [AIRFLOW_SETUP.md](AIRFLOW_SETUP.md)에서 Connections/Variables 설정
3. ⏭️ 스케줄 활성화 및 자동 실행 확인
4. ⏭️ 모니터링 및 알림 설정 (선택)
