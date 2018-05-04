# coding=utf-8
from .func import *


class Show(object):
	def info(self, disk_name):
		show_disk_info(disk_name)

	def overage(self):
		show_overage_disk()

	def err(self):
		show_err_smart_disk()

	def wearout(self):
		show_wearout_ssd()

	def list(self):
		show_disk_list()
