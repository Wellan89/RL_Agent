import argparse
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

def main():
	parser = argparse.ArgumentParser(description='Run commands')
	parser.add_argument('-n', '--workers-per-machine', type=int, default=4)
	parser.add_argument('-p', '--port-base-idx', type=int, default=12500)
	parser.add_argument('-f', '--first-machine-idx', type=int, default=300)
	parser.add_argument('-l', '--last-machine-idx', type=int, default=400)

	args = parser.parse_args()

	worker_idx = 0
	with open("cluster_ensimag_generated.cfg", "w") as file:
		file.write("[cluster]\n")
		for i in range(args.first_machine_idx, args.last_machine_idx + 1):
			machine = "ensipc{}".format(i)
			if ping(machine):
				for port in range(args.port_base_idx, args.port_base_idx + args.workers_per_machine):
					file.write("worker{}: {}:{}\n".format(worker_idx, machine, port))
					worker_idx += 1

		file.write("num_workers: {}\n".format(worker_idx))

if __name__ == "__main__":
	main()
