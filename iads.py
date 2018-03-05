# coding=utf-8
import fire
import os
from setting import iads_help_list
from apps.bios import Bios
from apps.mem import Mem
from apps.cpu import Cpu
from apps.phy import Phy
from apps.disk import Disk
from apps.net import Net
from apps.app_func import show_help


class Main(object):
	def __init__(self):
		self.help = show_help()
		self.bios = Bios()
		self.mem = Mem()
		self.cpu = Cpu()
		self.phy = Phy()
		self.disk = Disk()
		self.net = Net()

	def help(self):
		pass


if __name__ == '__main__':
	fire.Fire(Main)
