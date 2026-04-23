# Skill: Posture Reviewer (Reviewer)

## Purpose
Evaluates posture health by calculating neck tilt and head orientation using facial landmarks.

## Patterns
- **Reviewer**: Analyzes metrics against specific physical thresholds.
- **Defensive Design**: Uses hysteresis to prevent flickering alerts.

## Design Pattern: Reviewer Logic
1. Reads eye distance and nose-to-chin distance.
2. Filters for "Turning" (Yaw) to avoid noise during natural head movement.
3. Compares current ratio against calibrated baseline.
4. Outputs `PostureReport` with boolean state and detailed metrics.
