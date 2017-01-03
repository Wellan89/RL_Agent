import argparse
import os
import sys
from config import Config
from train import CommandsManager

def create_tmux_commands(config):
	cmds = CommandsManager(config.tmux_session)

	cmds.add_cmd(config.ps_server, None, "tmux kill-session")
	for i in range(len(config.workers)):
		cmds.add_cmd(config.workers[i], None, "tmux kill-session")

	return cmds.get_cmds()

def run():
	config = Config(False)

	cmds = create_tmux_commands(config)
	print("\n".join(cmds))
	os.system("\n".join(cmds))

if __name__ == "__main__":
	run()
