import argparse
import os
import sys
from config import Config
from train import CommandsManager

def create_tmux_commands(config):
	cmds = CommandsManager(config.tmux_session)

	cmds.add_cmd(config.ps_server, None, "tmux kill-session")
	workers = set([worker.split(":")[0] for worker in config.workers])
	for worker in workers:
		cmds.add_cmd(worker, None, "tmux kill-session")

	return cmds.get_cmds()

def run():
	config = Config(False, False)

	cmds = create_tmux_commands(config)
	print("\n".join(cmds))
	os.system("\n".join(cmds))

if __name__ == "__main__":
	run()
