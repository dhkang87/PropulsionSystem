# Twin Builder OCT Compatibility - Handoff Document

> 작성일: 2026-05-22  
> 브랜치: `fix/twin-builder-oct-compat`  
> 상태: **Turbojet_ex01 컴파일 + 400초 시뮬레이션 성공**

---

## 1. 프로젝트 개요

Modelica 라이브러리(PropulsionSystem, AircraftDynamics, FluidSystemComponents)를 **Ansys Twin Builder 2026 R1**의 OCT(Optimica Compiler Toolkit by Modelon) 컴파일러 + MSL 4.0에서 동작하도록 수정하는 작업.

---

## 2. 핵심 발견 (WhenPreTest01~04로 검증됨)

| 테스트 모델 | 패턴 | 결과 |
|-------------|-------|------|
| WhenPreTest01 | `when`/`pre()` + `discrete` | ✅ 통과 |
| WhenPreTest02 | `when`/`pre()` + `Real` | ✅ 통과 |
| WhenPreTest03 | `initial equation` + `discrete` | ❌ structurally singular |
| WhenPreTest04 | `equation` + `Real` (직접 할당) | ✅ 통과 |

**결론:**
- OCT는 `initial equation`을 연속 시스템 구조 분석에서 **제외**함
- `discrete` 변수에 `initial equation`만으로 값을 할당하면 방정식 부족으로 singular 판정
- **해법**: `discrete` 제거 → 일반 `Real` + `equation` 섹션에서 직접 할당

---

## 3. MSL 4.0 마이그레이션

| AS-IS (MSL 3.x) | TO-BE (MSL 4.0) |
|------------------|-----------------|
| `Modelica.SIunits` | `Modelica.Units.SI` |
| `Modelica.SIunits.Conversions.NonSIunits` | `Modelica.Units.NonSI` |
| `limitsAtInit` annotation | 제거 |
| `print("...")` | `Modelica.Utilities.Streams.print("...")` |
| `Real == Real` | `Real >= Real` (부동소수점 비교) |

적용 범위: PropulsionSystem 141+28 files, AircraftDynamics 1 commit, FluidSystemComponents 1 commit

---

## 4. 수정 완료 파일 목록

### PropulsionSystem - 1차 커밋 (5c0ef73)
- MSL bulk migration (141 SIunits + 28 NonSIunits files)
- `limitsAtInit` 제거 (9 files)
- `print()` → `Modelica.Utilities.Streams.print()` (18 files)
- `Real ==` → `>=` (MassFlowAtInit.mo)
- `connect()` inside if → equality equation (ConstrainVariable.mo)
- DefDesPt00 inheritance restructuring
- `when`/`pre()` 블록 제거 (CompressorBaseDefDesPt00, TurbineBaseDefDesPt00, NozzleBaseDefDesPt00)
- CmpCharTable01, TrbCharTable00, TrbCharTable01에서 when 블록 제거

### PropulsionSystem - 2차 커밋 (642ca90)
- `discrete` → 일반 `Real` (CompressorBase00, TurbineBase00, NozzleBase00, 3개 DefDesPt00)
- `initial equation` → `equation` 이동 (3개 BaseDefDesPt00 + NozzleBase00)
- NzlDefAeByFlowCharFixed00: initial algorithm 중복 제거
- TrbCharTable00: `PRdes_paramInput` 파라미터 추가
- TurbineTable_WcEff_NcPR00: n_Wc/n_eff 주석 해제 + 인덱스 [0]→[1], [1]→[2]
- CompressorBase00: `flagEffVal(start=0)` 추가
- Turbojet_ex01: `inertia1(phi(fixed=true, start=0))` 추가
- WhenPreTest01~04 진단 모델 추가

---

## 5. 주요 파일 구조

```
PropulsionSystem/
  BaseClasses/BasicElements/
    CompressorBase00.mo         ← discrete 제거
    CompressorBaseDefDesPt00.mo ← initial eq → equation 이동
    TurbineBase00.mo            ← discrete 제거
    TurbineBaseDefDesPt00.mo    ← initial eq → equation 이동
    NozzleBase00.mo             ← discrete 제거, PRdes in equation
    NozzleBaseDefDesPt00.mo     ← initial eq → equation 이동
  Elements/BasicElements/
    CmpCharTable00.mo           ← equation에서 fluid_1_des 직접 할당
    CmpCharTable01.mo           ← when 블록 제거
    TrbCharTable00.mo           ← when 제거, PRdes_paramInput 추가
    TrbCharTable01.mo           ← when 블록 제거
    NzlDefAeByFlowCharFixed00.mo ← 전부 equation으로 통합
  Subelements/
    TurbineTable_WcEff_NcPR00.mo ← n_Wc/n_eff 활성화, 인덱스 수정
  Examples/
    Test/WhenPreTest01~04.mo    ← OCT 호환성 테스트 모델
    Engines/Transient/Turbojet_ex01.mo ← 시뮬 성공 모델
```

---

## 6. 검증 방법

1. Twin Builder에서 PropulsionSystem 라이브러리 로드
2. `PropulsionSystem.Examples.Test.WhenPreTest01~04` 각각 Check Model (Ctrl+F7)
3. `PropulsionSystem.Examples.Engines.Transient.Turbojet_ex01` 시뮬레이션 (400초)

---

## 7. 다음 가능한 작업

- [ ] 다른 Turbojet 예제 (ex02 등) 컴파일 시도
- [ ] Turbofan 예제 확인
- [ ] pyAEDT 자동화 스크립트 (`tbTurbine_VHDL_AMS.ipynb`) 완성
- [ ] Compressor map 궤적 시각화
- [ ] Twin Builder에서 VHDL-AMS export 테스트

---

## 8. 관련 레포 & 브랜치

| 레포 | 브랜치 | 커밋 |
|------|--------|------|
| PropulsionSystem | `fix/twin-builder-oct-compat` | 5c0ef73, 642ca90 |
| AircraftDynamics | `fix/twin-builder-oct-compat` | 8bbc30d |
| FluidSystemComponents | `fix/twin-builder-oct-compat` | 39b7271 |
| pyAEDT_MoaEM | `TwinBuilder_TurboPJT` | (노트북 작업 중) |

---

## 9. Twin Builder 설정 참고

- Tools > Options > Modelica Compiler Options
- C-compiler: GCC(internal) / GCC(user) / Visual Studio (백엔드)
- 프론트엔드는 OCT 고정 (변경 불가)
- OCT는 Java 기반 (JRE 설정 있음)
- External Solver: CVode / Euler (시뮬레이션 단계)
