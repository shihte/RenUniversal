# Skill: Video Capture (Tool Wrapper)

## Purpose
Provides a thread-safe interface for capturing video frames from local cameras with automatic reconnection logic.

## Usage
- **Input**: Camera source index, target resolution.
- **Output**: Numpy frame array or None if unavailable.

## Patterns
- **Tool Wrapper**: Wraps OpenCV's `VideoCapture`.
- **Defensive Error Handling**: Implements exponential backoff for reconnections.

## Configuration
Managed via `CaptureConfig` Pydantic model.
