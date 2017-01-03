import argparse
import os
import sys
from config import Config

class CommandsManager:
	def __init__(self, session_name):
		self.machines_windows = {}
		self.session_name = session_name
		self.cmds = []

	def add_cmd(self, machine, window, cmd):
		if isinstance(cmd, (list, tuple)):
			cmd = " ".join(str(v) for v in cmd)

		machine = machine.split(":")[0]
		if machine == "127.0.0.1":
			machine = "localhost"

		if machine != "localhost":
			self.cmds.append("ssh -o StrictHostKeyChecking=no {}".format(machine))

		if window != None:
			known_windows = self.machines_windows.get(machine)
			if known_windows is None:
				self.cmds.append("tmux kill-session -t {}".format(self.session_name))
				self.cmds.append("tmux new-session -s {} -n {} -d".format(self.session_name, window))
				self.machines_windows[machine] = [window]
			else:
				if window not in known_windows:
					self.cmds.append("tmux new-window -t {} -n {}".format(self.session_name, window))
					self.machines_windows[machine].append(window)

			self.cmds.append("tmux send-keys -t {}:{} '{}' Enter".format(self.session_name, window, cmd))
			self.cmds.append("sleep 1")
		else:
			self.cmds.append(cmd)

		if machine != "localhost":
			self.cmds.append("exit")

	def get_cmds(self):
		return self.cmds

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
