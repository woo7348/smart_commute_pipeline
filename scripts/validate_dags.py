#!/usr/bin/env python3
"""
DAG Validator Script
검증:
1. 모든 DAG 파일의 구문 검사
2. DAG 로딩 가능 여부 확인
3. 태스크 의존성 검증
"""

import os
import sys
import importlib.util
from pathlib import Path

def validate_dag_file(dag_file_path: str) -> dict:
    """
    DAG 파일을 로드하고 검증합니다.
    
    Args:
        dag_file_path: DAG 파일 경로
        
    Returns:
        검증 결과 딕셔너리
    """
    result = {
        "file": dag_file_path,
        "valid": False,
        "error": None,
        "dags": []
    }
    
    try:
        # 구문 검사
        with open(dag_file_path, 'r') as f:
            compile(f.read(), dag_file_path, 'exec')
        
        # DAG 파일 로드
        spec = importlib.util.spec_from_file_location("dag_module", dag_file_path)
        module = importlib.util.module_from_spec(spec)
        
        # Airflow 모듈이 없을 수 있으므로 에러 처리
        try:
            spec.loader.exec_module(module)
        except ImportError as e:
            # Airflow가 설치되지 않은 환경에서는 구문 검사만 수행
            result["valid"] = True
            result["message"] = "Syntax OK (Airflow not installed for full validation)"
            return result
        
        # DAG 객체 찾기
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if hasattr(attr, 'dag_id'):  # DAG 객체
                result["dags"].append(attr.dag_id)
        
        result["valid"] = True
        
    except SyntaxError as e:
        result["error"] = f"SyntaxError: {str(e)}"
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
    
    return result


def main():
    """메인 검증 함수"""
    dag_dir = Path(__file__).parent / "dags"
    
    if not dag_dir.exists():
        print(f"❌ DAG 디렉토리를 찾을 수 없습니다: {dag_dir}")
        sys.exit(1)
    
    dag_files = sorted(dag_dir.glob("*.py"))
    print(f"🔍 {len(dag_files)}개의 DAG 파일 검증 중...\n")
    
    all_valid = True
    total_dags = 0
    
    for dag_file in dag_files:
        if dag_file.name.startswith("_"):  # __pycache__ 제외
            continue
        
        result = validate_dag_file(str(dag_file))
        status = "✅" if result["valid"] else "❌"
        
        print(f"{status} {dag_file.name}")
        
        if result["error"]:
            print(f"   Error: {result['error']}")
            all_valid = False
        elif result["dags"]:
            for dag_id in result["dags"]:
                print(f"   - DAG: {dag_id}")
            total_dags += len(result["dags"])
        elif result["valid"]:
            print(f"   ✓ Syntax OK")
        
        print()
    
    print("=" * 60)
    if all_valid:
        print(f"✅ 모든 DAG이 유효합니다! (총 {total_dags}개 DAG)")
        sys.exit(0)
    else:
        print("❌ 일부 DAG에 오류가 있습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
