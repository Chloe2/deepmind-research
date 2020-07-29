# Lint as: python3
# pylint: disable=g-bad-file-header
# Copyright 2020 DeepMind Technologies Limited. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or  implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
r"""Run an experiment.

Run GPE/GPI on task (1, -1) with a learned phi model and w by regression.


For example, first train a phi model with 3 dimenional phi:

python3 train_phi_model.py -- --logtostderr --use_random_tasks \
  --export_path=/tmp/option_keyboard/phi_model_3d --num_phis=3


Then train a keyboard:

python3 train_keyboard_with_phi.py -- --logtostderr \
  --export_path=/tmp/option_keyboard/keyboard_3d \
  --phi_model_path=/tmp/option_keyboard/phi_model_3d \
  --num_phis=2


Finally, evaluate the keyboard with w by regression.

python3 run_regressed_w_with_phi_fig4b.py -- --logtostderr \
  --phi_model_path=/tmp/option_keyboard/phi_model_3d \
  --keyboard_path=/tmp/option_keyboard/keyboard_3d/tfhub
"""

from absl import app
from absl import flags

import numpy as np
import tensorflow.compat.v1 as tf
import tensorflow_hub as hub

from option_keyboard import configs
from option_keyboard import environment_wrappers
from option_keyboard import experiment
from option_keyboard import scavenger
from option_keyboard import smart_module

from option_keyboard.gpe_gpi_experiments import regressed_agent

FLAGS = flags.FLAGS
flags.DEFINE_integer("num_episodes", 1000, "Number of training episodes.")
flags.DEFINE_string("phi_model_path", None, "Path to phi model.")
flags.DEFINE_string("keyboard_path", None, "Path to keyboard model.")


def main(argv):
  del argv

  # Load the keyboard.
  keyboard = smart_module.SmartModuleImport(hub.Module(FLAGS.keyboard_path))

  # Create the task environment.
  base_env_config = configs.get_fig4_task_config()
  base_env = scavenger.Scavenger(**base_env_config)
  base_env = environment_wrappers.EnvironmentWithLogging(base_env)

  base_env = environment_wrappers.EnvironmentWithLearnedPhi(
      base_env, FLAGS.phi_model_path)

  # Wrap the task environment with the keyboard.
  additional_discount = 0.9
  env = environment_wrappers.EnvironmentWithKeyboardDirect(
      env=base_env,
      keyboard=keyboard,
      keyboard_ckpt_path=None,
      additional_discount=additional_discount,
      call_and_return=False)

  # Create the player agent.
  agent = regressed_agent.Agent(
      batch_size=10,
      optimizer_name="AdamOptimizer",
      optimizer_kwargs=dict(learning_rate=1e-1,),
      init_w=np.random.normal(size=keyboard.num_cumulants) * 0.1,
  )

  experiment.run(
      env,
      agent,
      num_episodes=FLAGS.num_episodes,
      report_every=2,
      num_eval_reps=100)


if __name__ == "__main__":
  tf.disable_v2_behavior()
  app.run(main)
