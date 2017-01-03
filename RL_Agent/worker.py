#!/usr/bin/env python
import cv2
import go_vncdriver
import tensorflow as tf
import logging
import os
import time
from a3c import A3C
from envs import create_env
from config import Config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Disables write_meta_graph argument, which freezes entire process and is mostly useless.
class FastSaver(tf.train.Saver):
	def save(self, sess, save_path, global_step=None, latest_filename=None,
			 meta_graph_suffix="meta", write_meta_graph=True):
		super(FastSaver, self).save(sess, save_path, global_step, latest_filename,
									meta_graph_suffix, False)

def run(config, server):
	is_visualizer = (config.job_name == "visualizer")
	if is_visualizer:
		config.task = 0

	env = create_env(config.env_id, client_id=str(config.task), remotes=config.worker_remote)
	trainer = A3C(env, config.task)

	# Variable names that start with "local" are not saved in checkpoints.
	variables_to_save = [v for v in tf.all_variables() if not v.name.startswith("local")]
	init_op = tf.initialize_variables(variables_to_save)
	init_all_op = tf.initialize_all_variables()
	saver = FastSaver(variables_to_save)

	def init_fn(ses):
		logger.info("Initializing all parameters.")
		ses.run(init_all_op)

	tf_config = tf.ConfigProto(device_filters=["/job:ps", "/job:worker/task:{}/cpu:0".format(config.task)])
	logdir = os.path.join(config.log_dir, 'train')
	summary_dir = "{}/train_{}".format(config.log_dir, config.task)
	summary_writer = tf.train.SummaryWriter(summary_dir) if not is_visualizer else None
	logger.info("Events directory: {}".format(summary_dir))
	sv = tf.train.Supervisor(is_chief=(config.task == 0) if not is_visualizer else False,
							 logdir=logdir,
							 saver=saver,
							 summary_op=None,
							 init_op=init_op,
							 init_fn=init_fn,
							 summary_writer=summary_writer,
							 ready_op=tf.report_uninitialized_variables(variables_to_save),
							 global_step=trainer.global_step,
							 save_model_secs=30 if not is_visualizer else None,
							 save_summaries_secs=30 if not is_visualizer else None)

	num_global_steps = 100000000

	logger.info(
		"Starting session. If this hangs, we're mostly likely waiting to connect to the parameter server. " +
		"One common cause is that the parameter server DNS name isn't resolving yet, or is misspecified.")
	with sv.managed_session(server.target, config=tf_config) as sess, sess.as_default():
		sess.run(trainer.sync)	# copy weights from shared to local
		trainer.start(sess, summary_writer, is_visualizer)
		global_step = sess.run(trainer.global_step)
		logger.info("Starting {} at step=%d".format("visualization" if is_visualizer else "training"), global_step)
		while not sv.should_stop() and (not num_global_steps or global_step < num_global_steps or is_visualizer):
			if not is_visualizer:
				trainer.process(sess)
			else:
				sess.run(trainer.sync)	# copy weights from shared to local
				time.sleep(10.0)
			global_step = sess.run(trainer.global_step)

	# Ask for all the services to stop.
	sv.stop()
	logger.info('reached %s steps. worker stopped.', global_step)

def cluster_spec(config):
	"""
More tensorflow setup for data parallelism
"""
	cluster = {}
	cluster['ps'] = [config.ps_server]
	cluster['worker'] = config.workers
	return cluster

def main(_):
	"""
Setting up Tensorflow for data parallel work
"""

	config = Config(True)

	spec = cluster_spec(config)
	cluster = tf.train.ClusterSpec(spec).as_cluster_def()

	if config.job_name == "worker" or config.job_name == "visualizer":
		server = tf.train.Server(cluster, job_name="worker", task_index=config.task,
								 config=tf.ConfigProto(intra_op_parallelism_threads=1, inter_op_parallelism_threads=2))
		run(config, server)
	else:
		server = tf.train.Server(cluster, job_name="ps", task_index=config.task,
								 config=tf.ConfigProto(device_filters=["/job:ps"]))
		server.join()

if __name__ == "__main__":
	tf.app.run()
