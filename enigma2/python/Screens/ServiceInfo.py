from Components.HTMLComponent import HTMLComponent
from Components.GUIComponent import GUIComponent
from Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.NimManager import nimmanager
from ServiceReference import ServiceReference
from enigma import eListboxPythonMultiContent, eListbox, gFont, iServiceInformation, eServiceCenter
from Tools.Transponder import ConvertToHumanReadable

RT_HALIGN_LEFT = 0

TYPE_TEXT = 0
TYPE_VALUE_HEX = 1
TYPE_VALUE_DEC = 2
TYPE_VALUE_HEX_DEC = 3
TYPE_SLIDER = 4

def to_unsigned(x):
	return x & 0xFFFFFFFF

def ServiceInfoListEntry(a, b, valueType=TYPE_TEXT, param=4):
	print "b:", b
	if not isinstance(b, str):
		if valueType == TYPE_VALUE_HEX:
			b = ("0x%0" + str(param) + "x") % to_unsigned(b)
		elif valueType == TYPE_VALUE_DEC:
			b = str(b)
		elif valueType == TYPE_VALUE_HEX_DEC:
			b = ("0x%0" + str(param) + "x (%dd)") % (to_unsigned(b), b)
		else:
			b = str(b)

	return [
		#PyObject *type, *px, *py, *pwidth, *pheight, *pfnt, *pstring, *pflags;
		(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 200, 30, 0, RT_HALIGN_LEFT, ""),
		(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 200, 25, 0, RT_HALIGN_LEFT, a),
		(eListboxPythonMultiContent.TYPE_TEXT, 220, 0, 350, 25, 0, RT_HALIGN_LEFT, b)
	]

class ServiceInfoList(HTMLComponent, GUIComponent):
	def __init__(self, source):
		GUIComponent.__init__(self)
		self.l = eListboxPythonMultiContent()
		self.list = source
		self.l.setList(self.list)
		self.l.setFont(0, gFont("Regular", 23))
		self.l.setItemHeight(25)

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		self.instance.setContent(self.l)

TYPE_SERVICE_INFO = 1
TYPE_TRANSPONDER_INFO = 2

class ServiceInfo(Screen):
	def __init__(self, session, serviceref=None):
		Screen.__init__(self, session)
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.close,
			"cancel": self.close,
			"red": self.information,
			"green": self.pids,
			"yellow": self.transponder,
			"blue": self.tuner
		}, -1)

		if serviceref:
			self.type = TYPE_TRANSPONDER_INFO
			self["red"] = Label()
			self["green"] = Label()
			self["yellow"] = Label()
			self["blue"] = Label()
			info = eServiceCenter.getInstance().info(serviceref)
			self.transponder_info = info.getInfoObject(serviceref, iServiceInformation.sTransponderData)
			# info is a iStaticServiceInformation, not a iServiceInformation
			self.info = None
			self.feinfo = None
		else:
			self.type = TYPE_SERVICE_INFO
			self["red"] = Label(_("Service"))
			self["green"] = Label(_("PIDs"))
			self["yellow"] = Label(_("Multiplex"))
			self["blue"] = Label(_("Tuner status"))
			service = session.nav.getCurrentService()
			if service is not None:
				self.info = service.info()
				self.feinfo = service.frontendInfo()
				print self.info.getInfoObject(iServiceInformation.sCAIDs);
			else:
				self.info = None
				self.feinfo = None

		tlist = [ ]

		self["infolist"] = ServiceInfoList(tlist)
		self.onShown.append(self.information)

	def information(self):
		if self.type == TYPE_SERVICE_INFO:
			if self.session.nav.getCurrentlyPlayingServiceReference():
				name = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference()).getServiceName()
				refstr = self.session.nav.getCurrentlyPlayingServiceReference().toString()
			else:
				name = _("N/A")
				refstr = _("N/A")
			aspect = self.getServiceInfoValue(iServiceInformation.sAspect)
			if aspect in ( 1, 2, 5, 6, 9, 0xA, 0xD, 0xE ):
				aspect = _("4:3")
			else:
				aspect = _("16:9")
			width = self.info and self.info.getInfo(iServiceInformation.sVideoWidth) or -1
			height = self.info and self.info.getInfo(iServiceInformation.sVideoHeight) or -1
			if width != -1 and height != -1:
				Labels = ( (_("Name"), name, TYPE_TEXT),
						   (_("Provider"), self.getServiceInfoValue(iServiceInformation.sProvider), TYPE_TEXT),
						   (_("Aspect ratio"), aspect, TYPE_TEXT),
						   (_("Resolution"), "%dx%d" %(width, height), TYPE_TEXT),
						   (_("Namespace"), self.getServiceInfoValue(iServiceInformation.sNamespace), TYPE_VALUE_HEX, 8),
						   (_("Service reference"), refstr, TYPE_TEXT))
			else:
				Labels = ( (_("Name"), name, TYPE_TEXT),
						   (_("Provider"), self.getServiceInfoValue(iServiceInformation.sProvider), TYPE_TEXT),
						   (_("Aspect ratio"), aspect, TYPE_TEXT),
						   (_("Namespace"), self.getServiceInfoValue(iServiceInformation.sNamespace), TYPE_VALUE_HEX, 8),
						   (_("Service reference"), refstr, TYPE_TEXT))
			self.fillList(Labels)
		else:
			if self.transponder_info:
				tp_info = ConvertToHumanReadable(self.transponder_info)
				conv = { "tuner_type"			: _("Type"),
					 "system"			: _("System"),
					 "modulation"			: _("Modulation"),
					 "orbital_position"		: _("Orbital position"),
					 "frequency"			: _("Frequency"),
					 "symbol_rate"			: _("Symbol rate"),
					 "bandwidth"			: _("Bandwidth"),
					 "polarization"			: _("Polarization"),
					 "inversion"			: _("Inversion"),
					 "pilot"			: _("Pilot"),
					 "rolloff"			: _("Roll-off"),
					 "fec_inner"			: _("FEC"),
					 "code_rate_lp"			: _("Code rate LP"),
					 "code_rate_hp"			: _("Code rate HP"),
					 "constellation"		: _("Constellation"),
					 "transmission_mode"		: _("Transmission mode"),
					 "guard_interval" 		: _("Guard interval"),
					 "hierarchy_information"	: _("Hierarchy info") }
				Labels = [(conv[i], tp_info[i], TYPE_VALUE_DEC) for i in tp_info.keys()]
				self.fillList(Labels)

	def pids(self):
		if self.type == TYPE_SERVICE_INFO:
			Labels = ( (_("Video PID"), self.getServiceInfoValue(iServiceInformation.sVideoPID), TYPE_VALUE_HEX_DEC, 4),
					   (_("Audio PID"), self.getServiceInfoValue(iServiceInformation.sAudioPID), TYPE_VALUE_HEX_DEC, 4),
					   (_("PCR PID"), self.getServiceInfoValue(iServiceInformation.sPCRPID), TYPE_VALUE_HEX_DEC, 4),
					   (_("PMT PID"), self.getServiceInfoValue(iServiceInformation.sPMTPID), TYPE_VALUE_HEX_DEC, 4),
					   (_("TXT PID"), self.getServiceInfoValue(iServiceInformation.sTXTPID), TYPE_VALUE_HEX_DEC, 4),
					   (_("TSID"), self.getServiceInfoValue(iServiceInformation.sTSID), TYPE_VALUE_HEX_DEC, 4),
					   (_("ONID"), self.getServiceInfoValue(iServiceInformation.sONID), TYPE_VALUE_HEX_DEC, 4),
					   (_("SID"), self.getServiceInfoValue(iServiceInformation.sSID), TYPE_VALUE_HEX_DEC, 4))
			self.fillList(Labels)
	
	def showFrontendData(self, real):
		if self.type == TYPE_SERVICE_INFO:
			frontendData = self.feinfo and self.feinfo.getAll(real)
			Labels = self.getFEData(frontendData)
			self.fillList(Labels)
	
	def transponder(self):
		if self.type == TYPE_SERVICE_INFO:
			self.showFrontendData(True)
		
	def tuner(self):
		if self.type == TYPE_SERVICE_INFO:
			self.showFrontendData(False)

	def getFEData(self, frontendDataOrg):
		if frontendDataOrg and len(frontendDataOrg):
			frontendData = ConvertToHumanReadable(frontendDataOrg)
			tunerType = frontendDataOrg["tuner_type"]
			inputName = nimmanager.getNimSlotInputName(frontendData["slot_number"])
			if tunerType == "DVB-S":
				return ((_("NIM"), inputName, TYPE_TEXT),
						(_("Type"), frontendData["tuner_type"], TYPE_TEXT),
						(_("System"), frontendData["system"], TYPE_TEXT),
						(_("Modulation"), frontendData["modulation"], TYPE_TEXT),
						(_("Orbital position"), frontendData["orbital_position"], TYPE_VALUE_DEC),
						(_("Frequency"), frontendData["frequency"], TYPE_VALUE_DEC),
						(_("Symbol rate"), frontendData["symbol_rate"], TYPE_VALUE_DEC),
						(_("Polarization"), frontendData["polarization"], TYPE_TEXT),
						(_("Inversion"), frontendData["inversion"], TYPE_TEXT),
						(_("FEC"), frontendData["fec_inner"], TYPE_TEXT),
						(_("Pilot"), frontendData.get("pilot", None), TYPE_TEXT),
						(_("Roll-off"), frontendData.get("rolloff", None), TYPE_TEXT))
			elif tunerType == "DVB-C":
				return ((_("NIM"), inputName, TYPE_TEXT),
						(_("Type"), frontendData["tuner_type"], TYPE_TEXT),
						(_("Modulation"), frontendData["modulation"], TYPE_TEXT),
						(_("Frequency"), frontendData["frequency"], TYPE_VALUE_DEC),
						(_("Symbol rate"), frontendData["symbol_rate"], TYPE_VALUE_DEC),
						(_("Inversion"), frontendData["inversion"], TYPE_TEXT),
						(_("FEC"), frontendData["fec_inner"], TYPE_TEXT))
			elif tunerType == "DVB-T":
				return ((_("NIM"), inputName, TYPE_TEXT),
						(_("System"), frontendData["system"], TYPE_TEXT),
						(_("Type"), frontendData["tuner_type"], TYPE_TEXT),
						(_("Frequency"), frontendData["frequency"], TYPE_VALUE_DEC),
						(_("Inversion"), frontendData["inversion"], TYPE_TEXT),
						(_("Code rate LP"), frontendData.get("code_rate_lp", None), TYPE_TEXT),
						(_("Code rate HP"), frontendData.get("code_rate_hp", None), TYPE_TEXT),
						(_("Hierarchy info"), frontendData.get("hierarchy_information", None), TYPE_TEXT),
						(_("FEC"), frontendData.get("fec_inner", None), TYPE_TEXT),
						(_("PLP ID"), frontendData.get("plp_id", None), TYPE_VALUE_DEC),
						(_("Bandwidth"), frontendData["bandwidth"], TYPE_VALUE_DEC),
						(_("Constellation"), frontendData["constellation"], TYPE_TEXT),
						(_("Transmission mode"), frontendData["transmission_mode"], TYPE_TEXT),
						(_("Guard interval"), frontendData["guard_interval"], TYPE_TEXT))
		return [ ]

	def fillList(self, Labels):
		tlist = [ ]

		for item in Labels:
			if item[1] is None:
				continue;
			value = item[1]
			if len(item) < 4:
				tlist.append(ServiceInfoListEntry(item[0]+":", value, item[2]))
			else:
				tlist.append(ServiceInfoListEntry(item[0]+":", value, item[2], item[3]))

		self["infolist"].l.setList(tlist)

	def getServiceInfoValue(self, what):
		if self.info is None:
			return ""
		
		v = self.info.getInfo(what)
		if v == -2:
			v = self.info.getInfoString(what)
		elif v == -1:
			v = _("N/A")

		return v
