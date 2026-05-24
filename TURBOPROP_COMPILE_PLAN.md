# Turboprop Compile Sequence Plan

## Branch
- Name: `chore/turboprop-compile-sequence`
- Goal: Compile turboprop examples in increasing complexity and converge to Twin Builder compatibility.

## Scope
- Repository: PropulsionSystem
- Target models:
  1. `PropulsionSystem.Examples.Tests.DesignPoint.TurboProp001_001`
  2. `PropulsionSystem.Examples.Tests.OffDesignSim.TurboProp001_002`
  3. `PropulsionSystem.Examples.Tests.OffDesignSim.TurboProp002_001`
  4. `PropulsionSystem.Examples.Engines.OffDesignSim.Turboprop_ex01`

## Execution Order

### Phase 0 - Setup and Baseline
- [x] Create working branch.
- [x] Confirm model files and dependent table files exist.
- [ ] Confirm local library path set for PropulsionSystem, AircraftDynamics, FluidSystemComponents.

### Phase 1 - OpenModelica Fast Precheck
- [ ] Translate model #1.
- [ ] Resolve all class/type/path errors for #1.
- [ ] Translate model #2.
- [ ] Resolve all class/type/path errors for #2.
- [ ] Translate model #3.
- [ ] Resolve all class/type/path errors for #3.
- [ ] Translate model #4.
- [ ] Resolve all class/type/path errors for #4.

### Phase 2 - Twin Builder Final Check
- [ ] Compile model #1 in Twin Builder.
- [ ] Compile model #2 in Twin Builder.
- [ ] Compile model #3 in Twin Builder.
- [ ] Compile model #4 in Twin Builder.
- [ ] Resolve Twin Builder specific issues (annotation, path, medium, initialization).

### Phase 3 - Stabilization
- [ ] Re-run all 4 models in Twin Builder without new errors.
- [ ] Record known limitations and workaround notes.
- [ ] Prepare commit(s) by issue type.

## Working Rules
- Always fix lower complexity model first before moving to next.
- Keep each fix minimal and isolated.
- Do not include unrelated file changes in commits.

## Error Log Template

### Model
- Name:
- Tool: OpenModelica / Twin Builder
- Timestamp:

### Error Summary
- 

### Root Cause
- 

### Fix
- File:
- Change:

### Validation
- Command or action:
- Result:

## Progress Notes
- 2026-05-25: Branch `chore/turboprop-compile-sequence` created.
- 2026-05-25: Target model files verified present.
- 2026-05-25: OffDesign test models had missing relative map paths; updated to `modelica://PropulsionSystem/tableData/olds/...` in `TurboProp001_002` and `TurboProp002_001`.
- 2026-05-25: OpenModelica CLI (`omc`) is not available in current PATH, so Phase 1 translation execution is pending tool availability (or direct Twin Builder compile logs).
