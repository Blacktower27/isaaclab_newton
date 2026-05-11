# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Scooping (kinetic sand + arm) direct RL task."""

import gymnasium as gym

from . import agents

gym.register(
    id="Isaac-Scooping-Direct-v0",
    entry_point=f"{__name__}.scooping_env:ScoopingEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.scooping_env_cfg:ScoopingEnvCfg",
        "rl_games_cfg_entry_point": f"{agents.__name__}:rl_games_ppo_cfg.yaml",
    },
)