# TurboProp — Twin Builder 컴파일 전략 & 수정 컨텍스트

> 작성일: 2026-05-25  
> 브랜치: `fix/twin-builder-oct-compat`  
> 대상 툴: Ansys Twin Builder 2026.1 (OCT/Modelon backend)  
> 검증 툴: OpenModelica 1.26.3

---

## 1. 현재 상태 요약

| 항목 | 상태 |
|------|------|
| `checkModel(TurboProp001_001)` | ✅ 성공 (620 eq/620 var) |
| OpenModelica CLI `simulate()` | ✅ 성공 (dassl, 78 steps, 0.11s) |
| OMEdit GUI 시뮬레이션 | ⚠️ 0x00000001 (백엔드 내부오류 잔존 가능) |
| Twin Builder 라이브러리 로드 | ❌ 중복 등록 충돌 (해결 방법 아래) |
| Twin Builder 시뮬레이션 | 미시도 (로드 문제 먼저 해결 필요) |

---

## 2. Twin Builder 라이브러리 등록 규칙

### 에러 메시지
```
Command AddModelicaLibraryByFile failed:
  LibraryLoadingException: Failed to load library
  'D:\KangDH\ModelicaLib\PropulsionSystem\package.mo',
  the top level class 'PropulsionSystem' is already defined
  in loaded library 'D:\KangDH\ModelicaLib\PropulsionSystem'
```

### 원인
같은 라이브러리를 **폴더 경로**와 **package.mo 파일 경로**로 동시에 등록.

### 해결
1. Model Libraries 목록에서 `...\PropulsionSystem\package.mo` 항목 삭제
2. 폴더 경로만 유지:
   - `D:\KangDH\ModelicaLib\PropulsionSystem`
   - `D:\KangDH\ModelicaLib\FluidSystemComponents`
   - `D:\KangDH\ModelicaLib\AircraftDynamics`
3. SimModel 변경 팝업 → Compile and Update
4. 여전하면 Twin Builder 완전 종료 후 프로젝트 재오픈

---

## 3. 컴파일 추천 순서 (의존성 낮은 순)

### ① `Examples/Tests/DesignPoint/TurboProp001_001.mo`
- **가장 먼저** — DryAirNasa, 외부 맵 없음, 구조 단순
- 기본 라이브러리/연결 오류를 빨리 잡을 수 있음
- OpenModelica CLI에서 이미 성공 확인됨

### ② `Examples/Tests/OffDesignSim/TurboProp001_002.mo`
- 오프디자인 + 맵 기반 Cmp/Trb + 프로펠러 상세모델
- tableData 경로 해석 문제가 자주 생김 (Twin Builder에서 특히)

### ③ `Examples/Tests/OffDesignSim/TurboProp002_001.mo`
- 001_002보다 구속조건/회전축 설정이 더 빡빡함
- SetIndependent 사용 → 초기화 민감도 높음

### ④ `Examples/Engines/OffDesignSim/Turboprop_ex01.mo`
- PropulsionSystem 전용 혼합기체 Media 사용
- 최종 검증용 (모든 기본 안정성 확인 후)

---

## 4. 이미 적용된 Modelica 4 호환 수정 사항

### Turbine_Base.mo (핵심 수정)
```modelica
// BEFORE: 다중 if 분기 → BackendDAE 내부오류 유발
algorithm
  assert(PR < 0.0, ...);  // 방향 반대
  if ((0.0<fluid_2.p) and (0.0<fluid_1.p)) then
    h_2is := Medium.isentropicEnthalpy(fluid_2.p, fluid_1.state);
  elseif ((fluid_2.p<0.0) and (fluid_1.p<0.0)) then
    h_2is := Medium.isentropicEnthalpy(fluid_2.p, fluid_1.state);
  else
    h_2is := Medium.isentropicEnthalpy(-1.0*fluid_2.p, fluid_1.state);
  end if;

// AFTER: 단일 안전식
algorithm
  assert(0.0 < PR, ...);  // 방향 정상화
  h_2is := Medium.isentropicEnthalpy(
    noEvent(if fluid_2.p > 0.0 then fluid_2.p else -fluid_2.p),
    fluid_1.state);
```

### Compressor_Base.mo
```modelica
// BEFORE
assert(PR < 0.0, "PR of compressor element got less than 0", ...);
// AFTER
assert(0.0 < PR, "PR of compressor element got less than 0", ...);
```

### ElementFrame 인터페이스 (공통)
- `state.p.start`, `state.T.start` modifier 제거
- `fluid_*.state.p/T` 직접 접근 → `fluid_*.p/T`로 치환

### NozzleConv_Base.mo
- `fluid_1.state.p` → `fluid_1.p` 치환

### FlightToEngine.mo
- 오염 annotation 블록 제거
- 커넥터 대입식으로 정리
- 기본 medium을 DryAirNasa로 설정

### package.order 보강
- `Elements/BasicElements/package.order` — 누락 모델 대량 추가
- `Examples/package.order` — Tests, OpenCAEsymposium2019 추가
- `Examples/Tests/package.order` — DesignPoint 추가

---

## 5. Twin Builder 체크리스트 (모델별 실패 포인트 5개)

| # | 체크 항목 | 증상 | 대응 |
|---|-----------|------|------|
| 1 | 패키지 로드 | `LibraryLoadingException` 중복 | 폴더/package.mo 중복 제거 |
| 2 | tableData 경로 | `FileNotFoundException` | `Modelica.Utilities.Files.loadResource` 경로를 절대경로로 override |
| 3 | Medium 재선언 | `incompatible redeclaration` | `DryAirNasa` 기본 설정 확인, `constrainedby` 일치 |
| 4 | 초기값 불일치 | 시뮬레이션 수렴 실패 | `start` 값 명시, `fixed=false` 확인 |
| 5 | annotation 비호환 | 컴파일 경고/에러 | `textColor`(not fontColor), `FillPattern.Solid`, ASCII만 사용 |

---

## 6. 실전 팁

- OpenModelica CLI에서 먼저 `simulate()` 통과시킨 뒤 Twin Builder로 이동하면 디버깅 시간 대폭 감소
- Twin Builder OCT 백엔드는 OpenModelica보다 algorithm 블록 인접행렬 처리에 더 민감 → `noEvent`/`smooth` 적극 사용
- `version = ""` in package.mo는 Twin Builder에서 warning만 발생, 실패 원인은 아님

---

## 7. 파일 위치 참조

```
D:\KangDH\ModelicaLib\
├── PropulsionSystem\          ← fix/twin-builder-oct-compat 브랜치
│   ├── BaseClasses\BasicElements\
│   │   ├── Turbine_Base.mo    ← 핵심 수정
│   │   ├── Compressor_Base.mo ← assert 방향 수정
│   │   └── NozzleConv_Base.mo ← state 접근 수정
│   ├── Interfaces\ElementFrames\
│   │   ├── ElementFrame_2FluidPorts.mo
│   │   ├── ElementFrame_2FluidPorts_2ShaftPorts.mo
│   │   ├── ElementFrame_2FluidPorts_1HeatPort.mo
│   │   └── ElementFrame_1FluidPort_2ShaftPorts.mo
│   ├── Elements\BasicElements\
│   │   └── FlightToEngine.mo  ← 오염 제거
│   └── Examples\Tests\DesignPoint\
│       └── TurboProp001_001.mo ← 기준 테스트 모델
├── FluidSystemComponents\     ← fix/twin-builder-oct-compat
└── AircraftDynamics\          ← fix/twin-builder-oct-compat
```

---

## 8. 다음 세션 TODO

1. [ ] Twin Builder에서 라이브러리 중복 등록 제거 후 로드 성공 확인
2. [ ] TurboProp001_001 모델 Twin Builder에서 컴파일 성공 확인
3. [ ] tableData 경로 문제 발생 시 절대경로 override 적용
4. [ ] TurboProp002_001까지 순차적으로 진행
5. [ ] 시뮬레이션 실행 → 결과 pyAEDT로 추출 확인
