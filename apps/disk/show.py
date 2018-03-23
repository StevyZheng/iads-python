# coding=utf-8
from func import *


class Show(object):
	def info(self, disk_name):
		show_disk_info(disk_name)

	def overage(self):
		show_overage_disk()

	def power_count(self):
		pass

	def smart(self, diskname):
		pass

	def smartall(self):
		pass

	def err(self):
		show_err_smart_disk()

	def count(self):
		pass
