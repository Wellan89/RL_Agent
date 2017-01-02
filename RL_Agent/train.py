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
			known_windows = self.machines_windows.get(window)
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
	# for launching the TF workers and for launching tensorboard
	base_tf_cmd = [
		'CUDA_VISIBLE_DEVICES=', sys.executable, 'worker.py',
		'--config-file', config.config_file]

	cmds = CommandsManager(config.tmux_session)
	cmds.add_cmd("localhost", None, "mkdir -p {}".format(config.log_dir))

	cmds.add_cmd(config.ps_server, "ps", base_tf_cmd + ["--job-name", "ps"])
	for i in range(len(config.workers)):
		cmds.add_cmd(config.workers[i], "worker{}".format(i),
			base_tf_cmd + ["--job-name", "worker", "--task", str(i), "--worker-remote", config.remotes[i]])

	cmds.add_cmd("localhost", "tb",
		"{} -m tensorflow.tensorboard --logdir {} --port {}".format(sys.executable, config.log_dir, config.tensorboard_port))

	return cmds.get_cmds()

def run():
	config = Config(False)

	cmds = create_tmux_commands(config)
	print("\n".join(cmds))
	os.system("\n".join(cmds))

if __name__ == "__main__":
	run()
