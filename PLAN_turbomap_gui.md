# Plan: TPE331 Turbomap Workflow GUI (PyQt6)

## TL;DR
PyQt6 데스크톱 GUI로 TPE331 터보프롭 엔진 맵 스케일링 → Modelica 테이블 export → Twin Builder 시뮬레이션 → Operating Line 오버레이까지의 전체 워크플로우를 통합한다. 기존 `turbomap_data_utils.py` / `turbomap_plot_utils.py`를 백엔드로 재사용하고, pyAEDT 자동 연동 + CSV/MAT 수동 import를 모두 지원한다.

---

## Architecture

```
turbomap_gui/
├── main.py                  # QApplication entry point
├── main_window.py           # QMainWindow (탭 기반 레이아웃)
├── widgets/
│   ├── map_scaling_tab.py   # Tab 1: XML 로드 + 설계점 입력 + 스케일링
│   ├── map_viewer_tab.py    # Tab 2: matplotlib 맵 시각화 (Cmp/GGT/FPT 토글)
│   ├── modelica_export_tab.py  # Tab 3: 테이블 export + .mo 파라미터 패치
│   ├── simulation_tab.py    # Tab 4: pyAEDT 연동 or CSV import
│   └── opline_overlay_tab.py  # Tab 5: Operating line 오버레이
├── backend/
│   ├── modelica_table_exporter.py  # Modelica CombiTable2D txt 생성
│   ├── mo_param_patcher.py         # .mo 파일 파라미터 패치
│   └── tb_runner.py                # pyAEDT Twin Builder automation + CSV fallback
├── resources/
│   └── default_targets.json  # 기본 TPE331 설계점 저장
└── requirements.txt
```

---

## Steps

### Phase A: 프로젝트 스캐폴딩 + 기본 창
1. `turbomap_gui/` 폴더 생성, `main.py` + `main_window.py` (QTabWidget 기반 5탭 레이아웃)
2. `requirements.txt` 작성 (PyQt6, numpy, pandas, matplotlib, scipy, pyaedt)
3. matplotlib → Qt 임베딩 (`FigureCanvasQTAgg`)

### Phase B: Tab 1 — Map Scaling (*기존 유틸 재사용*)
4. XML 파일 선택 다이얼로그 (Compressor / GGT / FPT 각각)
5. 설계점 입력 폼 (QFormLayout): m_flow_des, PRdes, effDes, T1_des, p1_des
6. "Scale" 버튼 → `parse_compressor_xml()` / `parse_turbine_xml()` + `scale_*_map()` 호출
7. 스케일 결과 요약 테이블 (QTableWidget) — s_Wc, s_PR, s_eff, correction factor 진단
8. 결과를 내부 상태(dict)에 저장하여 다른 탭에서 참조

### Phase C: Tab 2 — Map Visualization (*기존 plot 함수 재사용*)
9. Compressor / GGT / FPT 토글 체크박스 (QCheckBox)
10. `plot_compressor_map()`, `plot_turbine_maps_2x2()` → `FigureCanvasQTAgg`에 임베드
11. "Refresh" 버튼으로 스케일링 변경 시 재그리기
12. Operating line 오버레이 on/off 토글 (Tab 5와 연동) — *depends on Phase E*

### Phase D: Tab 3 — Modelica Export
13. **`modelica_table_exporter.py`** 신규 작성:
    - Compressor: `Wc_NcRline`, `PR_NcRline`, `eff_NcRline` 3-table 파일 생성
    - Turbine: `Wc_NcPR`, `eff_NcPR` 2-table 파일 생성
    - 포맷: `#1\ndouble Name(rows,cols)\n[tab-separated matrix]` (PropulsionSystem 규격)
    - Nc=row axis, Rline(or PR)=column axis, 첫 행=column labels, 첫 열=row labels
14. **`mo_param_patcher.py`** 신규 작성:
    - 타겟 .mo 파일 경로 선택 (QFileDialog)
    - 정규식으로 `parameter Real NmechDes_paramInput = ...`, `PRdes_paramInput = ...` 등 패치
    - `switchTableDataLocation` → 사용자가 export한 table 경로로 변경
    - 미리보기 diff 표시 → 사용자 확인 후 저장
15. "Export Table" 버튼, "Patch .mo" 버튼

### Phase E: Tab 4 — Simulation (*parallel with Phase D*)
16. **Mode A (pyAEDT auto)**:
    - `pyaedt.TwinBuilder` 세션 연결 (AEDT project path 지정)
    - 시뮬레이션 실행 트리거
    - 결과 변수 선택 (Wc, PR, eta, Nmech, time 등)
    - 결과를 DataFrame으로 추출
17. **Mode B (Manual CSV/MAT import)**:
    - QFileDialog → CSV 또는 .mat 파일 로드
    - 컬럼 매핑 UI (어떤 열이 Wc/PR/Nc인지 지정)
18. 로드된 시뮬레이션 데이터를 내부 상태에 저장

### Phase F: Tab 5 — Operating Line Overlay
19. 시뮬레이션 데이터(Phase E)에서 operating point 시계열 추출
20. Compressor/GGT/FPT 중 사용자 선택(체크박스)에 따라 해당 맵 위에 오버레이
21. Time-colored scatter 또는 line plot (matplotlib colormap → 시간 진행 표현)
22. Design point + surge margin 표시
23. Export: 오버레이 플롯을 PNG/SVG로 저장

---

## Relevant Files

| File | Purpose |
|------|---------|
| `Jupyter/turbomap/turbomap_data_utils.py` | XML 파싱 + 설계점 스케일링 (Phase B 백엔드) |
| `Jupyter/turbomap/turbomap_plot_utils.py` | 시각화 함수 (Phase C 백엔드) |
| `tableData/table_Compressor_WcPReff_NcRline00.txt` | Modelica table 포맷 레퍼런스 |
| `tableData/table_Turbine_WcEff_NcPR00.txt` | Turbine table 레퍼런스 |
| `Elements/BasicElements/CmpCharTable00.mo` | .mo 파라미터 구조 레퍼런스 |
| `Elements/BasicElements/TrbCharTable00.mo` | 터빈 .mo 레퍼런스 |

---

## Modelica Table Format (PropulsionSystem 규격)

```
#1
double Wc_NcRline(16,12)   # Wc=f(Nc, Rline)
0       0.0873    0.1854    ...   (column headers = Nc values)
0.1     10.376    9.951     ...   (row label = Rline, then Wc data)
0.2     21.859    21.369    ...
...
```

- Compressor: 3 tables (Wc, PR, eff) indexed by (Nc, Rline)
- Turbine: 2 tables (Wc, eff) indexed by (Nc, PR)
- Tab-separated, `#1` header line, `double Name(rows,cols)` descriptor

---

## .mo Parameter Patch Targets (CmpCharTable00 example)

- `NmechDes_paramInput`, `PRdes_paramInput`, `effDes_paramInput`, `m_flow_1_des_paramInput`
- `switchTableDataLocation` → external file path
- Regex-based text substitution + diff preview before save

---

## Verification

1. Table export → PropulsionSystem `.txt` 파일과 포맷 비교
2. GUI smoke test: 탭 전환 + 버튼 → crash 없음
3. pyAEDT end-to-end: TB 세션 → 시뮬 → 변수 추출
4. 더미 CSV → Operating line 오버레이 정상 표시

---

## Decisions

- **PyQt6** (PySide6 API 호환, 추후 교체 가능)
- matplotlib `FigureCanvasQTAgg` — 기존 plot 함수 그대로 재사용
- 기존 `turbomap_*.py`는 `Jupyter/turbomap/`에 위치, GUI에서 sys.path로 import
- Modelica table 포맷: PropulsionSystem tableData 규격 준수 (탭 구분, `#1` 헤더)
- .mo 패치는 정규식 기반 텍스트 치환 (AST 파싱 불필요)
- Operating line 데이터: x=Wc (or PR for turbine), y=PR (or Wc for turbine) 시계열

---

## Further Considerations

1. **pyAEDT 버전 호환**: Twin Builder API는 pyaedt 0.8+ 필요. ANSYS 2026.1에서 `ansys.aedt.core` import 경로 변경 가능 → 런타임 감지
2. **테이블 축 convention**: 컴프레서(Nc, Rline) vs 터빈(Nc, PR) — exporter에서 명시적 체크
3. **2단계 배포**: Phase A~D 먼저 (시뮬 없이도 유용), Phase E~F는 pyAEDT 환경 확보 후 추가
