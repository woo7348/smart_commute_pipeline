# load_bus_seoul.py와 load_to_db.py NiFi 호환성 개선 상세 가이드

## 📝 개선 요약

두 파일을 Apache NiFi에서 사용하기 위해 다음과 같이 개선했습니다:

| 항목 | 기존 | 개선됨 |
|------|------|-------|
| **파일 경로** | 하드코딩 (`"output/bus_seoul_processed.csv"`) | 명령줄 인자 (`--input`) |
| **출력 형식** | 단순 print | 구조화된 JSON (`--json-output` 옵션) |
| **로깅** | 최소한 (print만) | 상세 로깅 (logging 모듈) |
| **에러 처리** | 중단만 가능 | 부분 성공, 경고 등 세분화 |
| **종료 코드** | 없음 | `sys.exit(0/1)` |
| **환경변수** | `.env` 파일만 | `.env` + 동적 인자 |

---

## 🎯 각 개선사항 설명

### 1️⃣ 명령줄 인자 (Command-line Arguments)

#### 기존 코드:
```python
def load_bus_to_db():
    df = pd.read_csv("output/bus_seoul_processed.csv")  # ❌ 하드코딩
```

#### 개선된 코드:
```python
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load bus data to PostgreSQL")
    parser.add_argument(
        "--input",
        type=str,
        default="output/bus_seoul_processed.csv",
        help="Input CSV file path"
    )
    args = parser.parse_args()
    
    result = load_bus_to_db(csv_path=args.input)
```

#### NiFi에서의 사용:
```bash
# 기본값 사용
python src/load_bus_seoul.py

# 커스텀 경로 지정
python src/load_bus_seoul.py --input /opt/nifi/data/bus_data.csv

# NiFi 변수 사용
python src/load_bus_seoul.py --input ${bus_csv_path} --json-output
```

---

### 2️⃣ JSON 포맷 출력

#### 기존 코드:
```python
print("✅ Bus data successfully loaded into PostgreSQL.")  # 파싱 어려움
```

#### 개선된 코드:
```python
import json
from datetime import datetime

result = {
    "status": "SUCCESS",           # 상태: SUCCESS, ERROR, PARTIAL_SUCCESS
    "message": f"Loaded {inserted_count}/{len(df)} rows",
    "row_count": inserted_count,   # 정수값으로 계산
    "errors": errors,              # 에러 목록 배열
    "timestamp": datetime.now().isoformat()  # ISO 8601 형식 시간
}

if args.json_output:
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

#### NiFi에서의 활용:

**예시 1: 상태 확인**
```
EvaluateJsonPath 프로세서:
  JSONPath: $.status
  Attribute Name: load.status
  
RouterOnAttribute:
  Route 1: ${load.status:equals('SUCCESS')}
  Route 2: ${load.status:equals('ERROR')}
```

**예시 2: 행 개수 추출**
```
EvaluateJsonPath 프로세서:
  JSONPath: $.row_count
  Attribute Name: rows.inserted
  
UpdateAttribute:
  last_sync_count: ${rows.inserted}
```

---

### 3️⃣ 상세 로깅

#### 기존 코드:
```python
print(f"📊 Loaded {len(df)} rows from {csv_path}")  # 로그 레벨 불명
print("✅ Bus data successfully loaded...")          # 파싱 불가능
```

#### 개선된 코드:
```python
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# 각 단계별 로깅
logger.info(f"📂 Reading CSV from: {csv_path}")
logger.info(f"🔗 Connecting to PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
logger.error(f"Row {idx} error: {str(e)}")
```

#### 로그 출력 예시:
```
2025-11-13 14:30:00,123 - INFO - 📂 Reading CSV from: output/bus_seoul_processed.csv
2025-11-13 14:30:00,456 - INFO - 📊 Loaded 1500 rows
2025-11-13 14:30:01,789 - INFO - 🔗 Connecting to PostgreSQL: localhost:5432/airflow
2025-11-13 14:30:02,012 - INFO - ✅ Database connection established
2025-11-13 14:30:02,345 - INFO - 📋 Creating table if not exists...
2025-11-13 14:30:02,678 - INFO - ✅ Table ready
2025-11-13 14:30:02,901 - INFO - 📥 Inserting 1500 rows...
2025-11-13 14:30:03,134 - INFO -   Progress: 100/1500 rows inserted
2025-11-13 14:30:10,456 - INFO - ✅ Successfully inserted 1500 rows
```

#### NiFi에서의 활용:
```
ExecuteProcess 프로세서:
  ✓ 표준 출력 캡처 (로그 메시지)
  
ParseLog 프로세서:
  ✓ 로그 레벨별 분석
  
RouteText 프로세서:
  ✓ ERROR 포함 시 실패 경로로 분기
```

---

### 4️⃣ 에러 처리 강화

#### 기존 코드:
```python
# 예외 발생 시 프로그램 중단됨
df = pd.read_csv(csv_path)
conn = psycopg2.connect(...)
```

#### 개선된 코드:
```python
def load_bus_to_db(csv_path: str) -> dict:
    try:
        # 1️⃣ 파일 존재 여부 확인
        if not os.path.exists(csv_path):
            return {
                "status": "ERROR",
                "message": f"File not found: {csv_path}",
                "errors": [f"File not found: {csv_path}"]
            }
        
        # 2️⃣ 데이터 읽기
        df = pd.read_csv(csv_path)
        if len(df) == 0:
            return {
                "status": "WARNING",
                "message": "CSV file is empty",
                "errors": []
            }
        
        # 3️⃣ 각 행별 에러 수집
        errors = []
        for idx, (_, row) in enumerate(df.iterrows(), 1):
            try:
                cur.execute(...)
            except Exception as e:
                errors.append(f"Row {idx} error: {str(e)}")
        
        # 4️⃣ 부분 성공 여부 판단
        return {
            "status": "SUCCESS" if len(errors) == 0 else "PARTIAL_SUCCESS",
            "message": f"Loaded {inserted_count}/{len(df)} rows",
            "errors": errors
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Critical error: {str(e)}",
            "errors": [str(e)]
        }
```

#### 3가지 상태:

| 상태 | 의미 | 예시 |
|------|------|------|
| **SUCCESS** | 모든 행 정상 적재 | 1500개 행 중 1500개 성공 |
| **PARTIAL_SUCCESS** | 일부 행 적재 실패 | 1500개 행 중 1498개 성공, 2개 에러 |
| **ERROR** | 심각한 오류 발생 | 파일 없음, DB 연결 실패 |

#### NiFi에서의 처리:
```
[ExecuteProcess]
      ↓
[EvaluateJsonPath: extract status]
      ↓
[RouteOnAttribute]
      ↙    ↓    ↘
SUCCESS  PARTIAL  ERROR
   ↓       ↓       ↓
[Log] [Alert] [Retry]
```

---

### 5️⃣ 종료 코드 (Exit Code)

#### 기존 코드:
```python
if __name__ == "__main__":
    load_bus_to_db()
    # 항상 성공으로 종료 (exit code 0)
```

#### 개선된 코드:
```python
if __name__ == "__main__":
    result = load_bus_to_db(csv_path=args.input)
    
    # 성공/실패 여부에 따라 다른 종료 코드
    sys.exit(0 if result["status"] in ["SUCCESS", "PARTIAL_SUCCESS"] else 1)
```

#### NiFi에서의 활용:
```
ExecuteProcess 프로세서:
  Exit Status: 0 → success 경로
  Exit Status: 1 → failure 경로
  
[ExecuteProcess]
      ↓
[RouteOnAttribute]
      ↙         ↘
(exit_status=0)  (exit_status!=0)
      ↓              ↓
 [Success]      [Retry/Alert]
```

---

## 🔄 완전한 NiFi 통합 예시

### 시나리오: 매일 오전 6시 버스 데이터 적재

#### NiFi 프로세스 그룹 구성:

```
┌─────────────────────────────────────────────────────┐
│ [Timer Trigger]                                     │
│   ↓                                                 │
│ [FetchFile: bus_seoul_processed.csv]                │
│   ↓                                                 │
│ [SetAttribute]                                      │
│   Attributes:                                       │
│   - input_path = ${file.path}                      │
│   - execution_time = ${now():toDate()}              │
│   ↓                                                 │
│ [ExecuteProcess]                                    │
│   Command: python3 src/load_bus_seoul.py            │
│   Args: --input ${input_path} --json-output         │
│   ↓                                                 │
│ [EvaluateJsonPath]                                  │
│   - $.status → load.status                          │
│   - $.row_count → rows.loaded                       │
│   - $.errors → load.errors                          │
│   ↓                                                 │
│ [RouteOnAttribute]                                  │
│   ↙                    ↓                    ↘        │
│ SUCCESS         PARTIAL_SUCCESS            ERROR    │
│   ↓                    ↓                      ↓      │
│ [Log]           [Log + Email]          [Retry]     │
│   ↓                    ↓                      ↓      │
│ [PutDatabaseRecord]   ...              [Send Alert]│
│   Insert into:                                      │
│   sync_log (timestamp, rows, status)                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### 각 프로세서 설정:

**1. Timer Trigger**
```
Scheduling Strategy: CRON
CRON Schedule: 0 6 * * *  (매일 6시)
```

**2. ExecuteProcess**
```
Command: python3
Command Arguments: src/load_bus_seoul.py --input ${input_path} --json-output
Working Directory: /opt/nifi/repository
Batch Size: 0
Output Handling: Stream to content
```

**3. EvaluateJsonPath**
```
Destination: flowfile-attribute

Property 1:
  Name: load.status
  JSONPath: $.status

Property 2:
  Name: rows.loaded
  JSONPath: $.row_count

Property 3:
  Name: load.message
  JSONPath: $.message
```

**4. RouteOnAttribute**
```
Relationship Configuration:
  SUCCESS: ${load.status:equals('SUCCESS')}
  PARTIAL_SUCCESS: ${load.status:equals('PARTIAL_SUCCESS')}
  ERROR: ${load.status:equals('ERROR')}
```

**5. PutDatabaseRecord (성공 케이스)**
```
Database Connection Pooling Service: PostgreSQL Connection Pool
Statement Type: INSERT
Catalog Name: airflow
Schema Name: public
Table Name: sync_audit_log
Column Mapping:
  - timestamp (FROM: ${execution_time})
  - table_name (FROM: 'bus_seoul_data')
  - rows_affected (FROM: ${rows.loaded})
  - status (FROM: ${load.status})
  - message (FROM: ${load.message})
```

---

## 🧪 로컬 테스트

### 테스트 1: JSON 출력 확인
```bash
python3 src/load_bus_seoul.py --input output/bus_seoul_processed.csv --json-output

# 예상 출력:
# {
#   "status": "SUCCESS",
#   "message": "Loaded 1500/1500 rows",
#   "row_count": 1500,
#   "errors": [],
#   "timestamp": "2025-11-13T14:30:00.123456"
# }
```

### 테스트 2: 커스텀 경로
```bash
python3 src/load_bus_seoul.py --input /tmp/test.csv --json-output
```

### 테스트 3: 에러 처리
```bash
python3 src/load_bus_seoul.py --input nonexistent.csv --json-output

# 예상 출력:
# {
#   "status": "ERROR",
#   "message": "File not found: nonexistent.csv",
#   "row_count": 0,
#   "errors": ["File not found: nonexistent.csv"],
#   "timestamp": "2025-11-13T14:30:05.654321"
# }
```

### 테스트 4: 종료 코드
```bash
python3 src/load_bus_seoul.py --input output/bus_seoul_processed.csv
echo "Exit code: $?"  # 0 (성공) 또는 1 (실패)
```

---

## 📚 참고: load_to_db.py도 동일하게 개선됨

```bash
# 날씨 데이터 적재 - 커스텀 경로
python3 src/load_to_db.py --input output/weather_20251113.csv --json-output

# 날씨 데이터 적재 - 기본 경로
python3 src/load_to_db.py
```

---

## ✅ NiFi 호환성 체크리스트

- [x] 명령줄 인자 지원 (`--input`, `--json-output`)
- [x] JSON 구조화 출력 (status, message, row_count, errors, timestamp)
- [x] 상세 로깅 (logging 모듈)
- [x] 에러 처리 강화 (3가지 상태: SUCCESS, PARTIAL_SUCCESS, ERROR)
- [x] 종료 코드 반환 (0/1)
- [x] 파일 존재 여부 확인
- [x] 진행상황 로깅 (100개 행마다 출력)
- [x] 타입 힌트 추가 (함수 서명)
- [x] Docstring 추가 (함수 문서화)
- [x] created_at 타임스탐프 테이블 컬럼 추가

---

## 🚀 다음 단계

1. Docker NiFi 환경 준비
2. 위 예시대로 프로세스 그룹 생성
3. 로컬에서 테스트 실행
4. NiFi UI에서 수동 실행 테스트
5. 스케줄 설정 (CRON)
6. 모니터링 및 알림 설정
