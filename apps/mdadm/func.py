# coding = utf-8
import sys
import inspect
from iadslib.IadsBaseContext import IadsBaseContext


class MdadmManager(IadsBaseContext):
	def __init__(self,
	             volume_name="iads_raid",
	             raid_level=0,
	             disks=None,
	             conf_file="/etc/mdadm.conf"):
		super(MdadmManager, self).__init__()
		self.raid_level = raid_level
		if isinstance(disks, dict):
			if len(dict) < 2:
				self.err("The number of disks is less than 2.")
		else:
			disks = None
			self.err("%s param disks is not a dict." % self.__class__.__name__)
		self.disks = disks
		self.volume_name = volume_name
		self.conf_name = conf_file
		

