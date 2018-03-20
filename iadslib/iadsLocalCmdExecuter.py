# coding=utf-8
try:
	from io import StringIO
except ImportError:
	from StringIO import StringIO
import subprocess
import threading
import time

from .iadsBaseContext import *

CMDEXECUTOR_LOGFILE = pjoin(IADS_LOG_DIR, "cmd_executor.log")


class IadsLocalCmdExecuter(IadsBaseContext):
	"""This is helper class to run shell command"""

	def __init__(self, enable_logging=False):
		if enable_logging:
			logFile = CMDEXECUTOR_LOGFILE
			self.logConfig = {
				"logfile": logFile,
				"logconsole": False
			}
			IadsBaseContext.__init__(self, name="cmd_executor", **self.logConfig)
		else:
			IadsBaseContext.__init__(self, logfile="")
		self.enable_cmd_logging = enable_logging
		self.exec_context = {}
		self.cmd_count = 0

	def add_command(self, cmd, name="NoName"):
		# Add a command to execute
		ind = self.cmd_count
		self.exec_context[ind] = {}
		self.exec_context[ind]["cmd"] = cmd
		self.exec_context[ind]["name"] = name
		self.cmd_count += 1
		return ind

	def clear(self):
		# clear all the commands and exec context
		self.exec_context.clear()
		self.cmd_count = 0
		return 0

	def run_cmd_parallel(self, timeout=30):
		""" The thread function to execute the command """

		def cmd_thread_func(ind, arg2, arg3):
			pipe = subprocess.PIPE
			if self.enable_cmd_logging:
				self.logger.info("child thread %d start execute cmd %s " % (ind, self.exec_context[ind]["cmd"]))
			self.exec_context[ind]["process"] = subprocess.Popen(self.exec_context[ind]["cmd"], shell=True, stdin=pipe,
			                                                     stdout=pipe, stderr=pipe)

			out, err = self.exec_context[ind]["process"].communicate()
			self.exec_context[ind]["stdout"] = out
			self.exec_context[ind]["stderr"] = err
			if self.exec_context[ind]["process"].returncode != 0:
				self.exec_context[ind]["returncode"] = 1
			else:
				self.exec_context[ind]["returncode"] = 0
			if self.enable_cmd_logging:
				self.logger.info("child thread %d complete execute cmd %s ret %d out %s err %s " % (
					ind, self.exec_context[ind]["cmd"], self.exec_context[ind]["returncode"], out, err))

		cmd_result = {}
		i = 0
		cmd_result["cmd_count"] = self.cmd_count
		if self.cmd_count == 0:
			return cmd_result

		thread = {}
		for i in range(self.cmd_count):
			thread[i] = threading.Thread(target=cmd_thread_func, args=(i, 0, 0))
			thread[i].start()

		for i in range(self.cmd_count):
			cmd_result[i] = {}
			cmd_result[i]["name"] = self.exec_context[i]["name"]
			thread[i].join(timeout)
			if thread[i].is_alive():
				self.exec_context[i]["process"].terminate()
				cmd_result[i]["timeout"] = 1
			else:
				cmd_result[i]["timeout"] = 0
			cmd_result[i]["stdout"] = self.exec_context[i]["stdout"]
			cmd_result[i]["stderr"] = self.exec_context[i]["stderr"]
			cmd_result[i]["returncode"] = self.exec_context[i]["returncode"]
		return cmd_result

	def run_cmd_single(self, cmd, timeout=-1, user_input=None):
		result = {}
		if timeout == 0:
			block_forever = True
		else:
			block_forever = False
		CHECK_INTERVAL = 0.02

		pipe = subprocess.PIPE
		if self.enable_cmd_logging:
			self.logger.info("create subprocess to execute cmd: " + cmd)
		if user_input is not None:
			proc = subprocess.Popen(cmd, shell=True, stdin=pipe, stdout=pipe, stderr=pipe)
			proc.stdin.write(user_input)
		else:
			proc = subprocess.Popen(cmd, shell=True, stdout=pipe, stderr=pipe)
		complete = False
		while block_forever or timeout > 0:
			if complete:
				break
			ret = proc.poll()
			if ret is not None:
				result["returncode"] = proc.returncode
				result["stdout"] = proc.stdout.read()
				result["strerr"] = proc.stderr.read()

				if self.enable_cmd_logging:
					self.logger.info("the cmd %s executed done, ret: %d, out: %s, err: %s" % (
						cmd, result["returncode"], result["stdout"], result["stderr"]))
					complete = True
					break

				time.sleep(CHECK_INTERVAL)
				if not block_forever:
					timeout -= CHECK_INTERVAL
		if not complete:
			proc.terminate()
			result["timeout"] = 1
		return result

	def run_cmd_serial(self, timeout=30, user_input=None):
		"""This is the single-thread version of run_cmd_parallel()."""

		def __convert_result(cur_result):
			result = {}
			cnt = 0
			for item in cur_result:
				if item["status"] == "TIMEOUT":
					item["timeout"] = 1
				else:
					item["timeout"] = 0
				del item["status"]
				result[cnt] = item
				cnt += 1
			return result

		if timeout == 0:
			block_forever = True
		else:
			block_forever = False
		CHECK_INTERVAL = 0.02
		cmd_list = self.exec_context.values()
		# start all the procs
		pipe = subprocess.PIPE
		for cmd in cmd_list:
			if self.enable_cmd_logging:
				self.logger.info("create subprocess to execute cmd: " + cmd["cmd"])
			if user_input is not None:
				proc = subprocess.Popen(cmd["cmd"], shell=True, stdin=pipe,
				                        stdout=pipe, stderr=pipe)
				proc.stdin.write(user_input)
				# outstring = proc.stdout.readline()
				# if re.search("(y/n)", outstring):
				# inputarg = raw_input (outstring + ":")

				# proc = subprocess.Popen(cmd["cmd"], shell=True, stdin=pipe,
				# stdout=pipe, stderr=pipe)
				# proc.stdin.write(inputarg + "\n")
				cmd["proc"] = proc
			else:
				proc = subprocess.Popen(cmd["cmd"], shell=True,
				                        stdout=pipe, stderr=pipe)
				cmd["proc"] = proc
		result_list = []
		while block_forever or timeout > 0:
			# if there is no cmd in cmd_list, then we are done
			if len(cmd_list) == 0:
				break
			# when task done, will first put into transfer list,
			# then migrate to result_list in the cycle.
			transfer_list = []
			for cmd in cmd_list:
				proc = cmd["proc"]
				ret = proc.poll()
				if ret is not None:
					cmd["status"] = "OK"
					cmd["returncode"] = proc.returncode
					cmd["stdout"] = proc.stdout.read()
					cmd["stderr"] = proc.stderr.read()
					transfer_list.append(cmd)

					if self.enable_cmd_logging:
						self.logger.info("the cmd %s executed done, ret: %d, out: %s, err: %s" % \
						                 (cmd["cmd"], cmd["returncode"], cmd["stdout"], cmd["stderr"]))
			for cmd in transfer_list:
				result_list.append(cmd)
				cmd_list.remove(cmd)
			time.sleep(CHECK_INTERVAL)
			if not block_forever:
				timeout -= CHECK_INTERVAL

			# for all the rest of cmd, stop them and mark
		for cmd in cmd_list:
			cmd["proc"].terminate()
			cmd["status"] = "TIMEOUT"
		# merge finished and timed out process result
		result_list += cmd_list
		for item in result_list:
			del item["proc"]
		return __convert_result(result_list)

	def is_command_timeout(self, cmd_result, cmd_index):
		if cmd_index in cmd_result:
			return int(cmd_result[cmd_index]["timeout"])
		return 1

	def get_command_count(self, cmd_result):
		if cmd_result is None:
			return 0
		if "cmd_count" in cmd_result.keys():
			return int(cmd_result["cmd_count"])
		return 0

	def get_command_result(self, cmd_result, cmd_index):
		cmd_ret = 1
		cmd_stdout = None
		cmd_stderr = None
		if cmd_index in cmd_result:
			if "returncode" in cmd_result[cmd_index]:
				cmd_ret = int(cmd_result[cmd_index]["returncode"])
			if "stdout" in cmd_result[cmd_index]:
				cmd_stdout = cmd_result[cmd_index]["stdout"]
			if "stderr" in cmd_result[cmd_index]:
				cmd_stderr = cmd_result[cmd_index]["stderr"]
		return cmd_ret, cmd_stdout, cmd_stderr

	def run_one_shell_cmd(self, cmd, timeout=30, user_input=None):
		"""This is to run a cmd in parallel and wait for them to complete"""
		result = self.run_cmd_single(cmd, timeout, user_input)
		if 'timeout' in result and result['timeout'] == 1:
			ret = 124
			out = err = None
		else:
			ret = result["returncode"]
			out = result["stdout"]
			err = result["stderr"]
		# make sure out and err are both strings
		if not out:
			out = ""
		if not err:
			err = ""
		return ret, out, err
