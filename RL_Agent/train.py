import argparse
import os
import sys
from config import Config

def new_tmux_cmd(session, window_name, cmd):
	if isinstance(cmd, (list, tuple)):
		cmd = " ".join(str(v) for v in cmd)
	return name, "tmux send-keys -t {}:{} '{}' Enter".format(session, window_name, cmd)

def create_tmux_commands(config):
	# for launching the TF workers and for launching tensorboard
	base_cmd = [
		'CUDA_VISIBLE_DEVICES=', sys.executable, 'worker.py',
		'--config-file', config.config_file]

	cmds_map = [new_tmux_cmd(config.tmux_session, "ps", base_cmd + ["--job-name", "ps"])]
	for i in range(len(config.workers)):
		cmds_map += [new_tmux_cmd(config.tmux_session,
			"w-{}".format(i), base_cmd + ["--job-name", "worker", "--task", str(i), "--worker-remote", config.remotes[i]])]

	cmds_map += [new_tmux_cmd(config.tmux_session, "tb", ["tensorboard --logdir {} --port {}".format(config.log_dir, config.tensorboard_port)])]
	cmds_map += [new_tmux_cmd(config.tmux_session, "htop", ["htop"])]

	windows = [v[0] for v in cmds_map]

	cmds = [
		"mkdir -p {}".format(config.log_dir),
		"tmux kill-session -t {}".format(config.tmux_session),
		"tmux new-session -s {} -n {} -d".format(config.tmux_session, windows[0]),
	]
	for w in windows[1:]:
		cmds += ["tmux new-window -t {} -n {}".format(config.tmux_session, w)]
	cmds += ["sleep 1"]
	for window, cmd in cmds_map:
		cmds += [cmd]

	return cmds



def run():
	config = Config(False)

	cmds = create_tmux_commands(config)
	print("\n".join(cmds))
	os.system("\n".join(cmds))

if __name__ == "__main__":
	run()
