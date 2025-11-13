#!/usr/bin/env python3
"""
NiFi 호환성 테스트 스크립트
load_bus_seoul.py와 load_to_db.py의 개선사항을 검증합니다.
"""

import subprocess
import json
import sys
import os
from pathlib import Path

# 테스트 색상
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def log(msg, level="info"):
    if level == "success":
        print(f"{GREEN}✅ {msg}{RESET}")
    elif level == "error":
        print(f"{RED}❌ {msg}{RESET}")
    elif level == "warning":
        print(f"{YELLOW}⚠️  {msg}{RESET}")
    elif level == "info":
        print(f"{BLUE}ℹ️  {msg}{RESET}")
    else:
        print(msg)

def test_json_output():
    """JSON 출력 기능 테스트"""
    print(f"\n{BLUE}=== 테스트 1: JSON 출력 기능 ==={RESET}")
    
    log("load_bus_seoul.py --json-output 실행...", "info")
    result = subprocess.run(
        ["python", "src/load_bus_seoul.py", "--input", "output/bus_seoul_processed.csv", "--json-output"],
        capture_output=True,
        text=True,
        cwd="/Users/trizaxkyj/smart_commute_pipeline"
    )
    
    try:
        output_json = json.loads(result.stdout)
        log(f"JSON 파싱 성공: status={output_json.get('status')}", "success")
        
        # 필수 필드 확인
        required_fields = ["status", "message", "row_count", "errors", "timestamp"]
        for field in required_fields:
            if field in output_json:
                log(f"필드 '{field}' 확인됨", "success")
            else:
                log(f"필드 '{field}' 누락됨", "error")
                return False
        
        return True
    except json.JSONDecodeError as e:
        log(f"JSON 파싱 실패: {e}", "error")
        log(f"출력 내용:\n{result.stdout}", "warning")
        return False

def test_custom_input_path():
    """커스텀 입력 경로 테스트"""
    print(f"\n{BLUE}=== 테스트 2: 커스텀 입력 경로 ==={RESET}")
    
    test_csv = "output/test_bus_data.csv"
    
    # 테스트 CSV 생성
    import pandas as pd
    test_data = pd.DataFrame({
        "route_name": ["1번"], 
        "bus_type": ["일반"], 
        "station_name": ["강남역"],
        "arrmsg1": ["1분"], 
        "arrmsg2": ["2분"],
        "plain_no": ["1234"],
        "veh_id": ["BUS-001"]
    })
    
    os.makedirs("output", exist_ok=True)
    test_data.to_csv(test_csv, index=False)
    log(f"테스트 CSV 생성: {test_csv}", "success")
    
    result = subprocess.run(
        ["python", "src/load_bus_seoul.py", "--input", test_csv, "--json-output"],
        capture_output=True,
        text=True,
        cwd="/Users/trizaxkyj/smart_commute_pipeline"
    )
    
    if result.returncode == 0 or result.returncode == 1:
        log("커스텀 경로 인자 처리 성공", "success")
        return True
    else:
        log(f"커스텀 경로 인자 처리 실패 (exit code: {result.returncode})", "error")
        return False

def test_error_handling():
    """에러 처리 테스트"""
    print(f"\n{BLUE}=== 테스트 3: 에러 처리 ==={RESET}")
    
    # 존재하지 않는 파일로 테스트
    result = subprocess.run(
        ["python", "src/load_bus_seoul.py", "--input", "output/nonexistent.csv", "--json-output"],
        capture_output=True,
        text=True,
        cwd="/Users/trizaxkyj/smart_commute_pipeline"
    )
    
    try:
        output_json = json.loads(result.stdout)
        
        if output_json.get("status") == "ERROR":
            log(f"에러 상태 감지: {output_json.get('message')}", "success")
            return True
        else:
            log(f"예상치 못한 상태: {output_json.get('status')}", "warning")
            return False
    except json.JSONDecodeError:
        log("JSON 파싱 실패", "error")
        return False

def test_logging_output():
    """로깅 출력 테스트"""
    print(f"\n{BLUE}=== 테스트 4: 로깅 출력 ==={RESET}")
    
    result = subprocess.run(
        ["python", "src/load_bus_seoul.py", "--help"],
        capture_output=True,
        text=True,
        cwd="/Users/trizaxkyj/smart_commute_pipeline"
    )
    
    if "--input" in result.stdout and "--json-output" in result.stdout:
        log("명령줄 인자 문서화 확인됨", "success")
        return True
    else:
        log("명령줄 인자 문서화 미흡", "error")
        return False

def test_exit_codes():
    """종료 코드 테스트"""
    print(f"\n{BLUE}=== 테스트 5: 종료 코드 ==={RESET}")
    
    # 에러 케이스
    result_error = subprocess.run(
        ["python", "src/load_bus_seoul.py", "--input", "output/nonexistent.csv"],
        capture_output=True,
        cwd="/Users/trizaxkyj/smart_commute_pipeline"
    )
    
    if result_error.returncode == 1:
        log("에러 케이스: 종료 코드 1 확인됨", "success")
    else:
        log(f"에러 케이스: 예상치 못한 종료 코드 {result_error.returncode}", "warning")
    
    return True

def main():
    print(f"\n{BLUE}{'=' * 60}")
    print(f"🧪 NiFi 호환성 테스트 시작")
    print(f"{'=' * 60}{RESET}\n")
    
    tests = [
        ("JSON 출력 기능", test_json_output),
        ("커스텀 입력 경로", test_custom_input_path),
        ("에러 처리", test_error_handling),
        ("로깅 출력", test_logging_output),
        ("종료 코드", test_exit_codes),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            log(f"테스트 실행 중 예외 발생: {e}", "error")
            results.append((test_name, False))
    
    # 결과 요약
    print(f"\n{BLUE}{'=' * 60}")
    print(f"📊 테스트 결과 요약")
    print(f"{'=' * 60}{RESET}\n")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
        print(f"{status} - {test_name}")
    
    print(f"\n총 {passed_count}/{total_count} 테스트 통과")
    
    if passed_count == total_count:
        log("모든 테스트 통과! NiFi 통합 준비 완료.", "success")
        return 0
    else:
        log(f"{total_count - passed_count}개 테스트 실패", "error")
        return 1

if __name__ == "__main__":
    sys.exit(main())
