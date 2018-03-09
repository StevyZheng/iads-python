# coding=utf-8
import fire
from setting import str_help_list
from apps.bios import Bios
from apps.mem import Mem
from apps.cpu import Cpu
from apps.phy import Phy
from apps.disk import Disk
from apps.net import Net


class Main(object):
	def __init__(self):
		self.help = str_help_list()
		self.bios = Bios()
		self.mem = Mem()
		self.cpu = Cpu()
		self.phy = Phy()
		self.disk = Disk()
		self.net = Net()


if __name__ == '__main__':
	fire.Fire(Main)
