# 수정된 주간 보고 생성 흐름 (Spring Orchestration 기준)

## 1. 주간 보고 생성 요청

1. **Vue Frontend**
   - PM이 주간 보고 생성 요청
   - 주간 보고 생성 API를 Spring Framework 서버로 전송

2. **API Gateway**
   - 인증 서버로 인증 요청 전달

3. **인증 서버**
   - 인증 검증 완료
   - 인증 성공 시 API Gateway로 결과 반환

4. **API Gateway → Spring Framework**
   - 인증 완료된 주간 보고 생성 요청 전달

---

## 2. Spring Framework (오케스트레이터 역할)

5. **Spring Framework**
   - 프로젝트 단위 권한 검증
   - 주차(`week_start`, `week_end`) 확정
   - 생성 기준 시각(`as_of_timestamp`) 확정
   - 멱등성 처리
     - 동일 프로젝트/주차에 대해 중복 생성 요청 차단
   - 주간 보고 생성 요청을 FASTAPI 서버로 전달

---

## 3. FASTAPI 서버 (생성 엔진 역할)

6. **FASTAPI 서버**
   - MariaDB에서 조회
     - 프로젝트 기본 사항
     - 금주 진행 사항
     - 완수 태스크(비고 제외)
     - 미완수 태스크(지연 사유 제외)
     - 다음 주 진행 사항
     - 회의록 / 일정 변경 로그 / 간트 / 이전 주간 보고
   - Qdrant(Vector DB)에서
     - 사내 일정 리스크 판단 기준 문서 검색
   - 조회된 DB 데이터 + 기준 문서를 바탕으로
     - 일정 리스크 분석 리포트 생성
   - 생성 결과를 Spring Framework로 반환

---

## 4. 생성 결과 처리

7. **Spring Framework**
   - FASTAPI 응답 수신
   - 주간 보고 초안(DRAFT) 및 일정 리스크 분석 리포트 저장
   - Vue Frontend로 초안 조회 응답 반환

8. **Vue Frontend**
   - PM이 생성된 주간 보고 검토
   - 비고 / 지연 사유 등 수동 수정

9. **Vue Frontend → Spring Framework**
   - 저장 또는 보류 요청

10. **Spring Framework**
    - 주간 보고 최종 저장
    - 추후 조회/수정 API 제공
