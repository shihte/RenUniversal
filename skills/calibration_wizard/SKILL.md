# Skill: Calibration Wizard (Inversion)

## Purpose
Establishes a physical baseline for the user's posture through guided sampling.

## Patterns
- **Inversion**: Pauses active detection to gather requirements/context from the user before proceeding.
- **Data Collection**: Samples facial geometry for a defined duration (3s) to ensure statistical stability.

## Design Pattern: Inversion Workflow
1. User triggers calibration.
2. Skill requests "Steady Pose" (Inversion point).
3. Skill collects N samples of eye and nose-chin distance.
4. Skill calculates mean baseline and returns control to the Pipeline.
