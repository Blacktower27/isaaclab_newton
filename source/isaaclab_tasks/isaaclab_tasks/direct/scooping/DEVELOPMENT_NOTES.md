# Scooping Environment Development Notes

This document summarizes all changes made while bringing up
`Isaac-Scooping-Direct-v0` on Newton + Implicit MPM.

## Goal

Build a minimal direct RL environment that:

- shows MPM particles in Newton visualizer,
- contains particles in a box-like container,
- works for multiple environments (`num_envs > 1`),
- stays reasonably fast and stable.

## Files Changed

- `source/isaaclab_tasks/isaaclab_tasks/direct/scooping/scooping_env.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scooping/scooping_env_cfg.py`
- `source/isaaclab_visualizers/isaaclab_visualizers/newton/newton_visualizer_cfg.py`
- `source/isaaclab_visualizers/isaaclab_visualizers/newton/newton_visualizer.py`

## Key Functional Changes

### 1) Scooping task registration and bootstrapping

- Verified task registration via:
  - `id="Isaac-Scooping-Direct-v0"`
  - env entry point to `scooping_env:ScoopingEnv`
  - env cfg entry point to `scooping_env_cfg:ScoopingEnvCfg`
- Added missing `agents` scaffolding and PPO config path so the task can be created.

### 2) Newton MPM callbacks for model build

In `ScoopingEnv`, callbacks are registered on Newton physics lifecycle:

- `PhysicsEvent.MODEL_INIT`:
  - register MPM custom attributes,
  - add ground plane,
  - add explicit static box colliders to the Newton builder,
  - emit particle grid.
- `PhysicsEvent.PHYSICS_READY`:
  - fill particle material arrays on `model.mpm`.

Why: this ensures the solver model has deterministic MPM colliders/particles,
instead of relying on USD import behavior for collision.

### 3) Visual container vs MPM collision container split

Current design intentionally separates:

- **visual container** in USD (`_spawn_container_cuboids`) for scene readability,
- **collision container** in Newton builder (`_add_container_mpm_colliders`) for
  reliable Implicit MPM collision.

The visual container has collision disabled to avoid double-collider effects.

### 4) Multi-env alignment fix

Issue observed:

- with `num_envs=2`, scene showed an extra center container and only center had
  particles.

Root cause:

- MPM colliders/particles were added once at world origin, while visual envs were cloned.

Fix:

- read `self.scene.env_origins`,
- for each origin, add container colliders and particle grid with origin offset.

Result:

- each env gets its own MPM container and particle volume.

### 5) Newton visualizer particle toggle

Added configurable particle display support:

- `NewtonVisualizerCfg.show_particles: bool = True`
- `NewtonVisualizer.initialize()` now applies:
  - `viewer.show_particles = cfg.show_particles` when supported.

Why:

- makes particle visibility explicit and configurable from visualizer config.

## Numeric Tuning (Current Baseline)

### Particle emitter (`scooping_env.py`)

- `emit_lo = (-0.13, -0.13, 0.055)`
- `emit_hi = ( 0.13,  0.13, 0.15 )`
- `particles_per_cell = 3`
- `initial_jitter = 0.10`
- `density = 1100.0`

### Container geometry/collision (`scooping_env.py`)

- width/depth/height: `0.35 / 0.35 / 0.08`
- wall thickness: `0.04`
- wall overlap: `0.01` (to reduce seam leakage)
- MPM collider friction: `0.6`
- MPM collider gap: `0.01`

### Solver config (`scooping_env_cfg.py`)

Current balanced values:

- `voxel_size = 0.02`
- `max_iterations = 250`
- `num_substeps = 4`

These were selected to avoid excessive slowdown while keeping leakage acceptable.

## Known Constraints and Lessons Learned

### USD compatibility with Implicit MPM colliders

Not all USD assets are compatible with Implicit MPM collision import.

Observed error:

- `NotImplementedError: Shape type 10 not supported`

This corresponds to `GeoType.CONVEX_MESH` in Newton, which is not handled in
the current Implicit MPM `_get_shape_mesh()` path used to build collider meshes.

Implication:

- A visually valid USD asset may still fail as an MPM collider source.
- Primitive builder colliders (`add_shape_box`) remain the most reliable path.

## Typical Run Commands

Single env bring-up:

```bash
./isaaclab.sh -p scripts/environments/zero_agent.py --task Isaac-Scooping-Direct-v0 --num_envs 1 --viz newton
```

Multi-env check:

```bash
./isaaclab.sh -p scripts/environments/zero_agent.py --task Isaac-Scooping-Direct-v0 --num_envs 2 --viz newton
```

## Next Recommended Improvements

1. Move emitter/container numeric constants into `ScoopingEnvCfg` to avoid code-side constants.
2. Add a small regression test for multi-env MPM placement (env-origin offset correctness).
3. Add optional debug metric: particles below floor threshold, to quantify leakage.
