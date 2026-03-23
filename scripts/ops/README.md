# Ops Scripts

This directory contains deployment-local operational scripts.

Rules:
- These scripts may validate host-specific paths, providers, or runtime assumptions.
- They are not repository-generic health checks unless explicitly parameterized and documented as such.
- Prefer environment variables for expected values when practical.
