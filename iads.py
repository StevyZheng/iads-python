# coding=utf-8
import fire
import os
from setting import iads_help_list
from apps.bios import Bios
from apps.mem import Mem
from apps.cpu import Cpu
from apps.phy import Phy
from apps.disk import Disk


class Main(object):
	def __init__(self):
		help_list = "iads help menu:" + os.linesep * 2
		for i in iads_help_list:
			help_list += i[0] + "    " + i[1] + os.linesep
		self.help = help_list
		self.bios = Bios()
		self.mem = Mem()
		self.cpu = Cpu()
		self.phy = Phy()
		self.disk = Disk()

	def help(self):
		pass


if __name__ == '__main__':
	fire.Fire(Main)
