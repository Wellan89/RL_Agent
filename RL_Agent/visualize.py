import argparse
import os
import sys
from config import Config
from train import CommandsManager

def create_tmux_commands(config):
	# for launching the TF workers and for launching tensorboard
	base_tf_cmd = [
		'CUDA_VISIBLE_DEVICES=', sys.executable, 'worker.py',
		'--config-file', config.config_file]

	cmds = CommandsManager(config.tmux_session)
	cmds.add_cmd("localhost", None, base_tf_cmd + ["--job-name", "visualizer"])

	return cmds.get_cmds()

def run():
	config = Config(False, False)

	cmds = create_tmux_commands(config)
	print("\n".join(cmds))
	os.system("\n".join(cmds))

if __name__ == "__main__":
	run()

