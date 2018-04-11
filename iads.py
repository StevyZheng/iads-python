# coding=utf-8
import sys
import fire
from setting import str_help_list
from linux import bin_exists
from apps.bios import Bios
from apps.mem import Mem
from apps.cpu import Cpu
from apps.phy import Phy
from apps.disk import Disk
from apps.net import Net
reload(sys)
sys.setdefaultencoding('utf-8')


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
	toot_list = ["lsscsi", "lsblk", "smartctl", "sas3ircu"]
	for i in toot_list:
		if not bin_exists(i):
			print("%s is not exists, please install." % i)
			exit(-1)
	fire.Fire(Main)
