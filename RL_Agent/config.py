import argparse
try:
	from configparser import ConfigParser
except ImportError:
	from ConfigParser import ConfigParser
import os
import platform

def ping(host):
	"""
	Returns True if host responds to a ping request
	"""

	# Ping parameters as function of OS
	ping_str = "-n 1" if platform.system().lower() == "windows" else "-c 1"

	# Ping
	host = host.split(":")[0]
	return os.system("ping " + ping_str + " " + host) == 0

class Config:
	def __init__(self, is_worker):
		args_parser = argparse.ArgumentParser(description='Run commands')
		args_parser.add_argument('-c', '--config-file', type=str, default='pong.cfg',
							help='Configuration file')

		if not is_worker:
			args_parser.add_argument('-s', '--tmux-session', type=str, default='a3c',
								help='The tmux session name')
			args_parser.add_argument('-r', '--remotes', default=None,
								help='The address of pre-existing VNC servers and '
									 'rewarders to use (e.g. -r vnc://localhost:5900+15900,vnc://localhost:5901+15901).')
		else:
			args_parser.add_argument('--task', type=int, default=0, help='Task index')
			args_parser.add_argument('--job-name', type=str, default="worker", help='worker or ps')
			args_parser.add_argument('--worker-remote', type=str, default=None,
								help='References to environments to create (e.g. --worker-remote 20), '
									 'or the address of pre-existing VNC server and '
									 'rewarder to use (e.g. --worker-remote vnc://localhost:5900+15900)')

		args = args_parser.parse_args()
		config = ConfigParser({
			'env_id': 'PongDeterministic-v3',
			'ps_server': 'localhost:12222',
			'num_workers': '1',
			'worker0': 'localhost:12223',
			'tensorboard_port': '12345',
			'cluster_file': ''
			})
		config.read(args.config_file)
		if config.get('cluster', 'cluster_file') != '':
			config.read(config.get('cluster', 'cluster_file'))

		self.config_file = args.config_file
		self.env_id = config.get('environment', 'env_id')

		self.ps_server = config.get('cluster', 'ps_server')
		assert(ping(self.ps_server))
		self.workers = [config.get('cluster', 'worker{}'.format(i)) for i in range(config.getint('cluster', 'num_workers'))]
		self.tensorboard_port = config.get('cluster', 'tensorboard_port')

		self.log_dir = 'logs/' + os.path.splitext(os.path.basename(self.config_file))[0]

		if not is_worker:
			self.tmux_session = args.tmux_session
			self.remotes = args.remotes
			if self.remotes is None:
				self.remotes = ['1'] * len(self.workers)
			else:
				self.remotes = remotes.split(',')
				assert(len(self.remotes) == len(self.workers))

			# Check we can reach all specified workers
			for worker in self.workers:
				assert(ping(worker))
		else:
			self.task = args.task
			self.job_name = args.job_name
			assert(self.job_name == "worker" or self.job_name == "ps")
			self.worker_remote = args.worker_remote
