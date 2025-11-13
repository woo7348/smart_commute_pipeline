# Apache NiFi 통합 가이드

## 📋 개요
이 문서는 `load_bus_seoul.py`와 `load_to_db.py`를 Apache NiFi에서 실행하기 위한 설정 및 사용법을 설명합니다.

---

## 🔄 개선사항

### ✨ NiFi 호환성 개선 사항

#### 1️⃣ **표준 입출력 (I/O) 지원**
- **기존**: 하드코딩된 파일 경로만 사용 → NiFi의 동적 흐름 제어 불가능
- **개선**: `--input` 명령줄 인자로 파일 경로 동적 지정 가능
- **용도**: NiFi의 `ExecuteStreamCommand` 또는 `ExecuteProcess` 프로세서에서 경로 전달 가능

#### 2️⃣ **JSON 포맷 결과 출력**
- **기존**: 단순 print 출력 (파싱 어려움)
- **개선**: `--json-output` 플래그로 구조화된 JSON 반환
- **용도**: NiFi의 `EvaluateJsonPath` 등으로 결과값 추출 및 분기 제어

#### 3️⃣ **상세 로깅**
- **기존**: 최소한의 로그만 출력
- **개선**: 프로세스의 각 단계별 상세 로그 (진행상황, 에러)
- **용도**: NiFi UI와 로그 파일에서 파이프라인 추적 용이

#### 4️⃣ **에러 처리 강화**
- **기존**: 에러 발생 시 프로세스 중단
- **개선**: 부분 성공(PARTIAL_SUCCESS), 경고(WARNING) 등으로 세분화
- **용도**: NiFi에서 우아한 재시도/분기 처리 가능

#### 5️⃣ **상태 코드 (Exit Code) 반환**
- **기존**: 없음
- **개선**: `sys.exit(0/1)` 로 성공/실패 명확히 구분
- **용도**: NiFi에서 프로세스 결과 판단 및 라우팅

---

## 🚀 NiFi에서의 사용법

### 방법 1: ExecuteProcess 프로세서 사용 (권장)

#### 설정 단계:
1. **프로세스 명령어**:
```bash
python src/load_bus_seoul.py --input ${input_csv_path} --json-output
```

2. **프로세서 속성** 설정:
| 속성 | 값 |
|------|-----|
| Command | `python` |
| Command Arguments | `src/load_bus_seoul.py --input ${input_csv_path} --json-output` |
| Working Directory | `/opt/nifi/repository` (또는 레포 경로) |
| Batch Size | `0` |
| Output handling | `Stream to content` |

3. **변수 설정** (ExecuteProcess 이전에 SetAttribute 프로세서):
```
input_csv_path: output/bus_seoul_processed.csv
```

4. **데이터 흐름**:
```
GetFile → TransformData → ExecuteProcess (load_bus_seoul.py) → EvaluateJsonPath → RouteOnAttribute
```

---

### 방법 2: InvokeHTTP + REST API (간접 방식)

만약 스크립트를 REST API로 래핑한다면:

```python
# api_wrapper.py
from flask import Flask, request, jsonify
import json
from load_bus_seoul import load_bus_to_db

app = Flask(__name__)

@app.route('/load-bus', methods=['POST'])
def load_bus_endpoint():
    data = request.json
    csv_path = data.get('csv_path', 'output/bus_seoul_processed.csv')
    result = load_bus_to_db(csv_path=csv_path)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)
```

NiFi 설정:
- `InvokeHTTP` → POST → `http://localhost:5000/load-bus`
- JSON 바디: `{"csv_path": "${csv_path}"}`

---

## 📊 출력 포맷 예시

### 성공 시:
```json
{
  "status": "SUCCESS",
  "message": "Loaded 1500/1500 rows",
  "row_count": 1500,
  "errors": [],
  "timestamp": "2025-11-13T14:30:00.123456"
}
```

### 부분 성공 시:
```json
{
  "status": "PARTIAL_SUCCESS",
  "message": "Loaded 1498/1500 rows",
  "row_count": 1498,
  "errors": [
    "Row 100 error: Invalid value for column TMP",
    "Row 500 error: Duplicate entry"
  ],
  "timestamp": "2025-11-13T14:30:05.654321"
}
```

### 에러 시:
```json
{
  "status": "ERROR",
  "message": "File not found: output/bus_seoul_processed.csv",
  "row_count": 0,
  "errors": ["File not found: output/bus_seoul_processed.csv"],
  "timestamp": "2025-11-13T14:30:10.987654"
}
```

---

## 🔧 NiFi 프로세서 조합 예시

### 1️⃣ 날씨 데이터 로드 플로우
```
[GetFile: weather_processed.csv]
         ↓
    [SetAttribute: set input_csv_path]
         ↓
    [ExecuteProcess: python load_to_db.py]
         ↓
    [EvaluateJsonPath: extract status]
         ↓
    [RouteOnAttribute: SUCCESS / ERROR]
         ↓         ↓
    [LogMessage] [LogMessage + SendError]
```

### 2️⃣ 버스 데이터 로드 플로우
```
[GetFile: bus_seoul_processed.csv]
         ↓
    [SetAttribute: set input_csv_path]
         ↓
    [ExecuteProcess: python load_bus_seoul.py]
         ↓
    [EvaluateJsonPath: extract row_count]
         ↓
    [UpdateAttribute: set db_status from JSON]
         ↓
    [PutDatabaseRecord: insert to audit_log]
```

### 3️⃣ 분기 처리
```
[ExecuteProcess]
         ↓
    [EvaluateJsonPath]
         ↓
    [RouteOnAttribute]
         ↓                  ↓
  status=SUCCESS    status=PARTIAL_SUCCESS
         ↓                  ↓
    [Success]        [Warning: notify]
         ↓                  ↓
    [LogMessage]      [PutEmail]
```

---

## 💡 NiFi 속성 설정 (EvaluateJsonPath 예시)

프로세서 설정:
```
Destination: flowfile-attribute
Return Type: scalar

Property 1:
  Name: db.status
  JSONPath: $.status

Property 2:
  Name: db.row_count
  JSONPath: $.row_count

Property 3:
  Name: db.errors
  JSONPath: $.errors
```

그 후 `RouteOnAttribute`에서:
```
Route 1: ${db.status:equals('SUCCESS')}
Route 2: ${db.status:equals('ERROR')}
Route 3: ${db.status:equals('PARTIAL_SUCCESS')}
```

---

## 🔒 환경변수 & 보안

### NiFi에서 환경변수 설정 방법:

#### 1️⃣ Docker Compose 환경변수
```yaml
services:
  nifi:
    environment:
      DB_HOST: postgres
      DB_NAME: airflow
      DB_USER: airflow
      DB_PASS: secure_password
      DB_PORT: 5432
```

#### 2️⃣ NiFi 속성 파일 (`nifi.properties`)
```properties
nifi.variable.registry.properties=/opt/nifi/conf/nifi-variables.properties
```

#### 3️⃣ 변수 파일 (`nifi-variables.properties`)
```properties
db.host=postgres
db.name=airflow
db.user=airflow
db.pass=secure_password
```

#### 4️⃣ NiFi 프로세서에서 사용
```
Command Arguments: src/load_bus_seoul.py --input ${input_path} --json-output
```

---

## 📝 테스트 방법

### 로컬 테스트 (Docker 없이)
```bash
# 1. CSV 파일 준비 (또는 테스트 데이터 생성)
python src/fetch_bus_seoul.py
python src/transform_bus_seoul.py

# 2. 로드 테스트 - 기본 실행
python src/load_bus_seoul.py

# 3. 로드 테스트 - 커스텀 경로
python src/load_bus_seoul.py --input output/bus_seoul_processed.csv

# 4. 로드 테스트 - JSON 출력 (NiFi 호환)
python src/load_bus_seoul.py --input output/bus_seoul_processed.csv --json-output
```

### NiFi에서의 테스트
1. NiFi UI 접속 → 새 프로세스 그룹 생성
2. ExecuteProcess 프로세서 추가
3. 명령어 입력: `python src/load_bus_seoul.py --input output/bus_seoul_processed.csv --json-output`
4. 프로세서 시작 → 결과 확인

---

## 🐛 트러블슈팅

### 문제 1: `FileNotFoundError: File not found`
**원인**: NiFi 컨테이너 내 작업 디렉토리 경로 불일치

**해결**:
```bash
# NiFi 컨테이너에서 경로 확인
docker exec -it nifi pwd
docker exec -it nifi ls -la /opt/nifi/

# 절대 경로 사용
python /opt/nifi/repository/src/load_bus_seoul.py --input /opt/nifi/repository/output/bus_seoul_processed.csv
```

### 문제 2: `ModuleNotFoundError: No module named 'pandas'`
**원인**: 필요한 Python 패키지가 NiFi 컨테이너에 설치되지 않음

**해결**:
```dockerfile
# NiFi Dockerfile에 추가
RUN pip install pandas psycopg2-binary python-dotenv

# 또는
RUN pip install -r requirements.txt
```

### 문제 3: DB 연결 실패 (`psycopg2.OperationalError`)
**원인**: NiFi 컨테이너에서 DB 호스트 접근 불가

**해결**:
```yaml
# docker-compose.yml
services:
  nifi:
    networks:
      - smart_commute_network
  postgres:
    networks:
      - smart_commute_network

networks:
  smart_commute_network:
    driver: bridge
```

---

## 📚 참고 자료
- [Apache NiFi 공식 문서](https://nifi.apache.org/docs)
- [NiFi ExecuteProcess 프로세서](https://nifi.apache.org/docs/nifi-docs/components/org.apache.nifi/nifi-standard-nar/1.16.3/org.apache.nifi.processors.standard.ExecuteProcess/)
- [NiFi EvaluateJsonPath](https://nifi.apache.org/docs/nifi-docs/components/org.apache.nifi/nifi-standard-nar/1.16.3/org.apache.nifi.processors.standard.EvaluateJsonPath/)

---

## ✅ 체크리스트

NiFi 통합 전 확인 사항:
- [ ] Python 패키지 설치 확인 (`pandas`, `psycopg2`, `python-dotenv`)
- [ ] 환경변수 설정 완료 (DB_HOST, DB_NAME, DB_USER, DB_PASS)
- [ ] CSV 파일 경로 확인 및 NiFi 컨테이너에서 접근 가능한지 확인
- [ ] 데이터베이스 연결 테스트 완료
- [ ] 로컬에서 스크립트 수동 실행 테스트 완료
- [ ] NiFi ExecuteProcess 프로세서 기본 설정 완료
- [ ] JSON 출력 검증 완료 (--json-output 플래그)
- [ ] 에러 핸들링 및 재시도 정책 설정 완료
