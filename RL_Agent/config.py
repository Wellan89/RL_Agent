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
	def __init__(self, is_worker, check_config=True):
		args_parser = argparse.ArgumentParser(description='Run commands')
		args_parser.add_argument('-c', '--config-file', type=str, help='Configuration file')

		if not is_worker:
			args_parser.add_argument('-s', '--tmux-session', type=str, default='a3c',
								help='The tmux session name')
			args_parser.add_argument('-r', '--remotes', default=None,
								help='The address of pre-existing VNC servers and '
									 'rewarders to use (e.g. -r vnc://localhost:5900+15900,vnc://localhost:5901+15901).')
		else:
			args_parser.add_argument('--task', type=int, default=0, help='Task index')
			args_parser.add_argument('--job-name', type=str, default="worker", help='worker, ps or visualizer')
			args_parser.add_argument('--worker-remote', type=str, default=None,
								help='References to environments to create (e.g. --worker-remote 20), '
									 'or the address of pre-existing VNC server and '
									 'rewarder to use (e.g. --worker-remote vnc://localhost:5900+15900)')

		args = args_parser.parse_args()
		assert(args.config_file is not None)
		config = ConfigParser({
			'model_name': 'universe_model',
			'model_learning_rate': '0.0001',
			'model_local_steps': '20',
			'model_layers_size': '256',
			'ps_server': 'localhost:12222',
			'num_workers': '1',
			'worker0': 'localhost:12223',
			'tensorboard_port': '12345',
			'cluster_file': ''
			})
		config.read(args.config_file)
		if config.get('cluster', 'cluster_file') != '':
			config.read('clusters/' + config.get('cluster', 'cluster_file'))

		self.config_file = args.config_file
		self.env_id = config.get('environment', 'env_id')

		self.model_name = config.get('model', 'model_name')
		self.model_learning_rate = config.getfloat('model', 'model_learning_rate')
		self.model_local_steps = config.getint('model', 'model_local_steps')
		self.model_layers_size = [int(s) for s in config.get('model', 'model_layers_size').split(',')]

		self.ps_server = config.get('cluster', 'ps_server')
		assert(not check_config or ping(self.ps_server))
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
				assert(not check_config or len(self.remotes) == len(self.workers))

			# Check we can reach all specified workers
			for worker in self.workers:
				assert(not check_config or ping(worker))
		else:
			self.task = args.task
			self.job_name = args.job_name
			assert(not check_config or self.job_name == "worker" or self.job_name == "ps" or self.job_name == "visualizer")
			self.worker_remote = args.worker_remote
