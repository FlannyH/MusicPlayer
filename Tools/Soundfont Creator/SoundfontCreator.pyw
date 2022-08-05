from tkinter import *
from tkinter import ttk
from tkinter import filedialog, messagebox
import os
import json
import InstrumentExporter

class Instrument:
	def __init__(self):
		self.name 						= "Untitled Instrument"
		self.attack 					= 255
		self.decay 						= 255
		self.sustain 					= 255
		self.release 					= 255
		self.type						= 0
		self.sample_source 				= ""
		self.loop_start 				= 0
		self.loop_enable				= False
		self.psg_length 				= 0
		self.psg_envelope_volume 		= 15
		self.psg_envelope_speed 		= 0
		self.psg_envelope_attack_mode 	= 0
		self.duty						= 0
		self.noise_shift_clock_freq		= 0
		self.noise_counter_width		= 0
		self.noise_dividing_ratio		= 0
		self.midi_mapping				= 0

class InstrumentEditor:
	def __init__(self, root):
		#Create main frame
		self.root = root
		mainframe = ttk.Frame(root, padding="3 3 12 12")
		mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
		root.columnconfigure(0, weight=1)
		root.rowconfigure(0, weight=1)

		#--KEYBOARD SHORTCUTS--
		self.root										.bind("<Control-n>", self.file_new)
		self.root										.bind("<Control-o>", self.file_open)
		self.root										.bind("<Control-s>", self.file_save)
		self.root										.bind("<Control-Shift-S>", self.file_save_as)

		#--CREATE VARIABLES--
		self.pulse_widgets 								= list()
		self.noise_widgets 								= list()
		self.wave_widgets 								= list()
		self.sample_widgets 							= list()
		self.instruments 								= list()
		self.last_sample_path							= None
		self.curr_instr_id 								= 0
		self.instrument_list_current_value 				= StringVar()
		self.instrument_name_curr 						= StringVar()
		self.instrument_type_curr 						= StringVar()
		self.instrument_sample_curr 					= StringVar()
		self.instrument_loop_start 						= IntVar()
		self.instrument_loop_enable						= BooleanVar()
		self.instrument_length_curr 					= IntVar()
		self.instrument_psg_envelope_volume_curr 		= IntVar()
		self.instrument_psg_envelope_speed_curr 		= IntVar()
		self.instrument_psg_envelope_attack_mode_curr 	= BooleanVar()
		self.instrument_attack 							= IntVar()
		self.instrument_decay 							= IntVar()
		self.instrument_sustain 						= IntVar()
		self.instrument_release 						= IntVar()
		self.instrument_duty							= StringVar()
		self.instrument_noise_shift_clock_freq			= IntVar()
		self.instrument_noise_dividing_ratio			= IntVar()
		self.instrument_noise_counter_width				= BooleanVar()
		self.instrument_midi_mapping					= StringVar()
		
		self.instrument_loop_start						.set(0)
		self.instrument_length_curr						.set(0)
		self.instrument_psg_envelope_volume_curr		.set(10)
		self.instrument_psg_envelope_speed_curr			.set(1)

		self.instrument_file_curr						= None
		self.title										= "Instrument Creator"
		root.title(self.title)
	
		#--CREATE WIDGETS--
		#Instrument list combobox
		self.combobox_instrument_list 				= ttk.Combobox(mainframe, textvariable=self.instrument_list_current_value, width=25, state="readonly")
		self.combobox_instrument_list				.grid(column=0, row=0, columnspan=2, sticky="ew")
		self.combobox_instrument_list				.bind("<<ComboboxSelected>>", self.change_instrument)
		
		#Instrument name
		self.label_name 							= ttk.Label(mainframe, text='Name:')
		self.entry_name 							= ttk.Entry(mainframe, textvariable=self.instrument_name_curr)
		self.entry_name								.bind("<KeyPress>", self.apply_instrument_values)
		self.entry_name								.bind("<KeyRelease>", self.apply_instrument_values)
		self.label_name								.grid(column=0, row=1, sticky="w")
		self.entry_name								.grid(column=1, row=1, sticky="ew")

		#Instrument mapping
		self.label_mapping							= ttk.Label(mainframe,text="Program Mapping:")
		self.combobox_mapping						= ttk.Combobox(mainframe, textvariable=self.instrument_midi_mapping, width=25, state="readonly")
		self.combobox_mapping						.bind("<<ComboboxSelected>>", self.apply_instrument_values)
		self.label_mapping							.grid(column=0, row=2, sticky="w")
		self.combobox_mapping						.grid(column=1, row=2, sticky="ew")

		#Get instrument names from file
		instrument_names = list()
		i = 1
		for name in open("midi_program_names.txt", "r").readlines():
			name = name.replace("\n","").replace("\r","")
			instrument_names.append(name)
			i += 1
		self.combobox_mapping['values'] = instrument_names
		
		#ADSR frame
		self.frame_adsr 							= ttk.Frame(mainframe)
		self.frame_adsr								.grid(column=0, row=3, columnspan=2, rowspan=4)
		
		#ADSR sliders
		self.scale_attack 							= ttk.Scale(self.frame_adsr, orient=VERTICAL, from_=0, to=255, variable=self.instrument_attack)
		self.scale_decay 							= ttk.Scale(self.frame_adsr, orient=VERTICAL, from_=0, to=255, variable=self.instrument_decay)
		self.scale_sustain 							= ttk.Scale(self.frame_adsr, orient=VERTICAL, from_=255, to=0, variable=self.instrument_sustain)
		self.scale_release 							= ttk.Scale(self.frame_adsr, orient=VERTICAL, from_=0, to=255, variable=self.instrument_release)
		self.scale_attack							.grid(column=0, row=0)
		self.scale_decay							.grid(column=1, row=0)
		self.scale_sustain							.grid(column=2, row=0)
		self.scale_release							.grid(column=3, row=0)
		self.scale_attack							.bind("<ButtonRelease>", self.apply_instrument_values)
		self.scale_decay							.bind("<ButtonRelease>", self.apply_instrument_values)
		self.scale_sustain							.bind("<ButtonRelease>", self.apply_instrument_values)
		self.scale_release							.bind("<ButtonRelease>", self.apply_instrument_values)
		self.spinbox_attack 						= ttk.Spinbox(self.frame_adsr, from_=0, to=255, width=5, command=self.fix_values, textvariable=self.instrument_attack)
		self.spinbox_decay 							= ttk.Spinbox(self.frame_adsr, from_=0, to=255, width=5, command=self.fix_values, textvariable=self.instrument_decay)
		self.spinbox_sustain 						= ttk.Spinbox(self.frame_adsr, from_=0, to=255, width=5, command=self.fix_values, textvariable=self.instrument_sustain)
		self.spinbox_release 						= ttk.Spinbox(self.frame_adsr, from_=0, to=255, width=5, command=self.fix_values, textvariable=self.instrument_release)
		self.spinbox_attack							.bind("<KeyPress>", self.apply_instrument_values)
		self.spinbox_attack							.bind("<KeyRelease>", self.apply_instrument_values)
		self.spinbox_decay							.bind("<KeyPress>", self.apply_instrument_values)
		self.spinbox_decay							.bind("<KeyRelease>", self.apply_instrument_values)
		self.spinbox_sustain						.bind("<KeyPress>", self.apply_instrument_values)
		self.spinbox_sustain						.bind("<KeyRelease>", self.apply_instrument_values)
		self.spinbox_release						.bind("<KeyPress>", self.apply_instrument_values)
		self.spinbox_release						.bind("<KeyRelease>", self.apply_instrument_values)
		self.label_attack 							= ttk.Label(self.frame_adsr, text="Attack")
		self.label_decay 							= ttk.Label(self.frame_adsr, text="Decay")
		self.label_sustain 							= ttk.Label(self.frame_adsr, text="Sustain")
		self.label_release 							= ttk.Label(self.frame_adsr, text="Release")
		self.spinbox_attack							.grid(column=0, row=1)
		self.spinbox_decay							.grid(column=1, row=1)
		self.spinbox_sustain						.grid(column=2, row=1)
		self.spinbox_release						.grid(column=3, row=1)
		self.label_attack							.grid(column=0, row=2)
		self.label_decay							.grid(column=1, row=2)
		self.label_sustain							.grid(column=2, row=2)
		self.label_release							.grid(column=3, row=2)
		self.sample_widgets.append(self.scale_attack)
		self.sample_widgets.append(self.scale_decay)
		self.sample_widgets.append(self.scale_sustain)
		self.sample_widgets.append(self.scale_release)
		self.sample_widgets.append(self.spinbox_attack)
		self.sample_widgets.append(self.spinbox_decay)
		self.sample_widgets.append(self.spinbox_sustain)
		self.sample_widgets.append(self.spinbox_release)
		self.sample_widgets.append(self.label_attack)
		self.sample_widgets.append(self.label_decay)
		self.sample_widgets.append(self.label_sustain)
		self.sample_widgets.append(self.label_release)
		
		#Create/Remove instrument button
		self.frame_instrument_buttons				= ttk.Frame(mainframe)
		self.frame_instrument_buttons				.grid(column=4, row=0, sticky="w")
		self.button_new_instrument 					= ttk.Button(self.frame_instrument_buttons, text="New", command=self.press_new_instrument)
		self.button_remove_instrument 				= ttk.Button(self.frame_instrument_buttons, text="Remove", command=self.press_remove_instrument)
		self.button_new_instrument					.grid(column=4, row=0, sticky="ew")
		self.button_remove_instrument				.grid(column=5, row=0, sticky="e")
		
		#Frames left and right
		self.frame_settings 						= ttk.Frame(mainframe)
		self.frame_settings							.grid(column=4,row=1, rowspan=5, sticky="nwse")
		
		#Create preview button
		self.button_preview 						= ttk.Button(mainframe, text="Preview", command=self.press_preview,)
		self.button_preview							.grid(column=4, row=0, columnspan=1, sticky='e')
		
		#Instrument type combobox
		self.label_instrument_type 					= ttk.Label(self.frame_settings, text="Instrument Type:")
		self.combobox_instrument_type				= ttk.Combobox(self.frame_settings, textvariable=self.instrument_type_curr, state="readonly")
		self.combobox_instrument_type['values'] 	= ['Sample Channel', 'Pulse Channel 1', 'Pulse Channel 2', "Wavetable Channel", "Noise Channel"]
		self.combobox_instrument_type				.bind("<<ComboboxSelected>>", self.apply_instrument_values)
		self.label_instrument_type					.grid(column=0, row=1, sticky='ew')
		self.combobox_instrument_type				.grid(column=1, row=1, sticky='ew', columnspan = 2)
		
		#Sample wave selector
		self.label_sample_source 					= ttk.Label(self.frame_settings, text="Sample Source:")
		self.frame_sample_source 					= ttk.Frame(self.frame_settings)
		self.entry_sample_source 					= ttk.Entry(self.frame_sample_source, textvariable=self.instrument_sample_curr)
		self.button_sample_source					= ttk.Button(self.frame_sample_source, text="...", command=self.press_sample_source, width=2)
		self.entry_sample_source					.bind("<KeyPress>", self.apply_instrument_values)
		self.entry_sample_source					.bind("<KeyRelease>", self.apply_instrument_values)
		self.label_sample_source					.grid(column=0, row=2, sticky='ew')
		self.frame_sample_source					.grid(column=1, row=2, sticky='ew', columnspan = 2)
		self.entry_sample_source					.grid(column=0, row=0, sticky='ew')
		self.button_sample_source					.grid(column=1, row=0, sticky='ew', columnspan = 2)
		self.sample_widgets.append(self.label_sample_source)
		self.sample_widgets.append(self.frame_sample_source)
		self.sample_widgets.append(self.entry_sample_source)
		self.sample_widgets.append(self.button_sample_source)
		self.wave_widgets.append(self.label_sample_source)
		self.wave_widgets.append(self.frame_sample_source)
		self.wave_widgets.append(self.entry_sample_source)
		self.wave_widgets.append(self.button_sample_source)
		
		#Loop start
		self.label_loop_start 						= ttk.Label(self.frame_settings, text="Loop Start:")
		self.spinbox_loop_start 					= ttk.Spinbox(self.frame_settings, from_=0, to=(2**31)-1, textvariable=self.instrument_loop_start, command=self.apply_instrument_values)
		self.label_loop_start						.grid(column=0, row=3, sticky='ew')
		self.spinbox_loop_start						.grid(column=1, row=3, sticky='ew', columnspan = 2)
		self.sample_widgets.append(self.label_loop_start)
		self.sample_widgets.append(self.spinbox_loop_start)

		#Loop enable
		self.label_loop_enable						= ttk.Label(self.frame_settings, text="Loop Enable:")
		self.checkbutton_loop_enable				= ttk.Checkbutton(self.frame_settings, variable=self.instrument_loop_enable, command=self.apply_instrument_values)
		self.label_loop_enable						.grid(column=0, row=4, sticky="ew")
		self.checkbutton_loop_enable				.grid(column=1, row=4, sticky="ew")
		self.sample_widgets.append(self.label_loop_enable)
		self.sample_widgets.append(self.checkbutton_loop_enable)
		
		#PSG length
		self.label_psg_length 						= ttk.Label(self.frame_settings, text="PSG Length:")
		self.spinbox_psg_length 					= ttk.Spinbox(self.frame_settings, from_=0, to=31, textvariable=self.instrument_length_curr, command=self.apply_instrument_values)
		self.label_psg_length						.grid(column=0, row=4, sticky='ew')
		self.spinbox_psg_length						.grid(column=1, row=4, sticky='ew', columnspan = 2)
		self.pulse_widgets.append(self.label_psg_length)
		self.pulse_widgets.append(self.spinbox_psg_length)
		self.noise_widgets.append(self.label_psg_length)
		self.noise_widgets.append(self.spinbox_psg_length)
		self.wave_widgets.append(self.label_psg_length)
		self.wave_widgets.append(self.spinbox_psg_length)
		
		#PSG envelope
		self.label_psg_envelope_volume 				= ttk.Label(self.frame_settings, text="PSG Envelope Volume:")
		self.label_psg_envelope_speed 				= ttk.Label(self.frame_settings, text="PSG Envelope Speed:")
		self.label_psg_envelope_attack_mode 		= ttk.Label(self.frame_settings, text="PSG Envelope Attack Mode Toggle:")
		self.scale_psg_envelope_volume 				= ttk.Scale(self.frame_settings, command=self.fix_values, orient=HORIZONTAL, from_=0, to=15, variable=self.instrument_psg_envelope_volume_curr)
		self.spinbox_psg_envelope_volume			= ttk.Spinbox(self.frame_settings, command=self.fix_values, width=5, from_=0, to=15, textvariable=self.instrument_psg_envelope_volume_curr)
		self.scale_psg_envelope_speed 				= ttk.Scale(self.frame_settings, command=self.fix_values, orient=HORIZONTAL, from_=0, to=7, variable=self.instrument_psg_envelope_speed_curr)
		self.spinbox_psg_envelope_speed				= ttk.Spinbox(self.frame_settings, command=self.fix_values, width=5, from_=0, to=7, textvariable=self.instrument_psg_envelope_speed_curr)
		self.checkbutton_psg_envelope_attack_mode 	= ttk.Checkbutton(self.frame_settings, variable=self.instrument_psg_envelope_attack_mode_curr, command=self.apply_instrument_values)
		
		self.label_psg_envelope_volume        		.grid(column=0, row=5, sticky='ew')
		self.label_psg_envelope_speed         		.grid(column=0, row=6, sticky='ew')
		self.label_psg_envelope_attack_mode   		.grid(column=0, row=7, sticky='ew')
		self.scale_psg_envelope_volume      		.grid(column=1, row=5, sticky='ew')
		self.spinbox_psg_envelope_volume      		.grid(column=2, row=5, sticky='ew')
		self.scale_psg_envelope_speed       		.grid(column=1, row=6, sticky='ew')
		self.spinbox_psg_envelope_speed      		.grid(column=2, row=6, sticky='ew')
		self.checkbutton_psg_envelope_attack_mode	.grid(column=1, row=7, sticky='ew')

		self.pulse_widgets.append(self.label_psg_envelope_volume)
		self.pulse_widgets.append(self.label_psg_envelope_speed)
		self.pulse_widgets.append(self.label_psg_envelope_attack_mode)
		self.pulse_widgets.append(self.scale_psg_envelope_volume)
		self.pulse_widgets.append(self.scale_psg_envelope_speed)
		self.pulse_widgets.append(self.spinbox_psg_envelope_volume)
		self.pulse_widgets.append(self.spinbox_psg_envelope_speed)
		self.pulse_widgets.append(self.checkbutton_psg_envelope_attack_mode)
		
		self.noise_widgets.append(self.label_psg_envelope_volume)
		self.noise_widgets.append(self.label_psg_envelope_speed)
		self.noise_widgets.append(self.label_psg_envelope_attack_mode)
		self.noise_widgets.append(self.scale_psg_envelope_volume)
		self.noise_widgets.append(self.scale_psg_envelope_speed)
		self.noise_widgets.append(self.spinbox_psg_envelope_volume)
		self.noise_widgets.append(self.spinbox_psg_envelope_speed)
		self.noise_widgets.append(self.checkbutton_psg_envelope_attack_mode)

		#PSG duty
		self.label_psg_duty 							= ttk.Label(self.frame_settings, text="PSG Duty:")
		self.combobox_psg_duty							= ttk.Combobox(self.frame_settings, textvariable=self.instrument_duty, state="readonly")
		self.combobox_psg_duty['values'] 				= ['12.5%', '25%', '50%', "75%"]
		self.combobox_psg_duty							.bind("<<ComboboxSelected>>", self.apply_instrument_values)
		
		self.label_psg_duty								.grid(column=0, row=8, sticky="ew")
		self.combobox_psg_duty							.grid(column=1, row=8, sticky="ew")

		self.pulse_widgets.append(self.label_psg_duty)
		self.pulse_widgets.append(self.combobox_psg_duty)

		#PSG noise frequencies
		self.label_noise_shift_clock_freq				= ttk.Label(self.frame_settings, text="Noise Shift Clock Frequency:")
		self.label_noise_dividing_ratio					= ttk.Label(self.frame_settings, text="Noise Dividing Ratio:")
		self.label_noise_counter_width					= ttk.Label(self.frame_settings, text="Noise Counter Width:")
		self.scale_noise_shift_clock_freq				= ttk.Scale(self.frame_settings, from_=0, to=15, variable=self.instrument_noise_shift_clock_freq, command=self.fix_values)
		self.spinbox_noise_shift_clock_freq				= ttk.Spinbox(self.frame_settings, width=5, from_=0, to=15, textvariable=self.instrument_noise_shift_clock_freq, command=self.fix_values)
		self.scale_noise_dividing_ratio					= ttk.Scale(self.frame_settings, from_=0, to=7, variable=self.instrument_noise_dividing_ratio, command=self.fix_values)
		self.spinbox_noise_dividing_ratio				= ttk.Spinbox(self.frame_settings, width=5, from_=0, to=7, textvariable=self.instrument_noise_dividing_ratio, command=self.fix_values)
		self.checkbutton_noise_counter_width			= ttk.Checkbutton(self.frame_settings, variable=self.instrument_noise_counter_width, command=self.apply_instrument_values)

		self.label_noise_shift_clock_freq				.grid(column=0, row=9, sticky="ew")
		self.label_noise_dividing_ratio					.grid(column=0, row=10, sticky="ew")
		self.label_noise_counter_width					.grid(column=0, row=11, sticky="ew")
		self.scale_noise_shift_clock_freq				.grid(column=1, row=9, sticky="ew")
		self.spinbox_noise_shift_clock_freq				.grid(column=2, row=9, sticky="ew")
		self.scale_noise_dividing_ratio					.grid(column=1, row=10, sticky="ew")
		self.spinbox_noise_dividing_ratio				.grid(column=2, row=10, sticky="ew")
		self.checkbutton_noise_counter_width			.grid(column=1, row=11, sticky="ew", columnspan = 2)

		self.noise_widgets.append(self.label_noise_shift_clock_freq)
		self.noise_widgets.append(self.label_noise_dividing_ratio)
		self.noise_widgets.append(self.label_noise_counter_width)
		self.noise_widgets.append(self.scale_noise_shift_clock_freq)
		self.noise_widgets.append(self.spinbox_noise_shift_clock_freq)
		self.noise_widgets.append(self.scale_noise_dividing_ratio)
		self.noise_widgets.append(self.spinbox_noise_dividing_ratio)
		self.noise_widgets.append(self.checkbutton_noise_counter_width)

		#Menu bar
		self.menubar								= Menu(root)

		self.filemenu 								= Menu(self.menubar, tearoff=0)
		self.filemenu								.add_command(label="New", command=self.file_new)
		self.filemenu								.add_command(label="Open", command=self.file_open)
		self.filemenu								.add_command(label="Save", command=self.file_save)
		self.filemenu								.add_command(label="Save As", command=self.file_save_as)
		self.filemenu								.add_command(label="Export", command=self.file_export)
		self.filemenu								.add_separator()
		self.filemenu								.add_command(label="Exit", command=self.file_exit)
		self.menubar								.add_cascade(label="File", menu=self.filemenu)

		self.helpmenu 								= Menu(self.menubar, tearoff=0)
		self.helpmenu								.add_command(label="About", command=self.help_about)
		self.menubar								.add_cascade(label="Help", menu=self.helpmenu)
		
		root.config(menu=self.menubar)

		self.file_new()
	
	def file_new(self, *args):
		print ("file_new")
		#Clear file variables
		self.instrument_file_curr = None

		#Reset title
		self.title = "Instrument Creator - untitled*"
		self.root.title(self.title)

		#Clear instruments list, and create a new one
		self.instruments = list()
		self.instruments.append(Instrument())
		self.curr_instr_id = 0
		self.instruments[self.curr_instr_id].midi_mapping = self.combobox_mapping['value'][0]
		self.update_ui_elements()

	def file_open(self, *args):
		print ("file_open")
		#Open a file dialog, set the instrument file variable to be the returned file path
		self.instrument_file_curr = filedialog.askopenfilename(filetypes=[("Instrument List", "*.json")], multiple=False, initialdir=os.getcwd())

		#Update the title
		self.title = "Instrument Creator - " + os.path.split(self.instrument_file_curr)[-1]
		self.root.title(self.title)

		#Read the file data
		file = open(self.instrument_file_curr, "r")
		json_data = json.load(file)
		self.instruments = list()
		for dict_instr in json_data["instruments"]:
			instrument = Instrument()
			instrument.name 					= dict_instr["name"] 					
			instrument.attack 					= dict_instr["attack"] 				
			instrument.decay 					= dict_instr["decay"] 				
			instrument.sustain 					= dict_instr["sustain"] 				
			instrument.release 					= dict_instr["release"] 				
			instrument.type 					= dict_instr["type"] 					
			instrument.sample_source 			= dict_instr["sample_source"] 		
			instrument.loop_start 				= dict_instr["loop_start"] 			
			instrument.loop_enable 				= dict_instr["loop_enable"] 			
			instrument.psg_length 				= dict_instr["psg_length"] 			
			instrument.psg_envelope_volume 		= dict_instr["psg_envelope_volume"] 	
			instrument.psg_envelope_speed 		= dict_instr["psg_envelope_speed"] 	
			instrument.psg_envelope_attack_mode	= dict_instr["psg_envelope_attack_mode"]
			instrument.duty						= dict_instr["duty"]
			instrument.noise_shift_clock_freq	= dict_instr["noise_shift_clock_freq"]
			instrument.noise_counter_width		= dict_instr["noise_counter_width"]
			instrument.noise_dividing_ratio		= dict_instr["noise_dividing_ratio"]
			instrument.midi_mapping				= dict_instr["midi_mapping"]
			self.instruments.append(instrument)

		self.curr_instr_id = json_data["curr_inst_id"]
		self.last_sample_path = json_data["last_sample_path"]
		self.update_ui_elements()

	def file_save(self, *args):
		print ("file_save")
		#If output file hasn't been set yet, open the save_as menu instead
		if self.instrument_file_curr == None:
			self.file_save_as()
			return

		#Change title to remove the trailing *
		if self.title.endswith("*"):
			self.title = self.title[:-1]
		self.root.title(self.title)

		#Save the file to a json file
		file = open(self.instrument_file_curr, "w")
		
		instruments_list = list()
		for instrument in self.instruments:
			dict_instr = dict()
			dict_instr["name"] 						= instrument.name
			dict_instr["attack"] 					= instrument.attack
			dict_instr["decay"] 					= instrument.decay
			dict_instr["sustain"] 					= instrument.sustain
			dict_instr["release"] 					= instrument.release
			dict_instr["type"] 						= instrument.type
			dict_instr["sample_source"] 			= instrument.sample_source
			dict_instr["loop_start"] 				= instrument.loop_start
			dict_instr["loop_enable"] 				= instrument.loop_enable
			dict_instr["psg_length"] 				= instrument.psg_length
			dict_instr["psg_envelope_volume"] 		= instrument.psg_envelope_volume
			dict_instr["psg_envelope_speed"] 		= instrument.psg_envelope_speed
			dict_instr["psg_envelope_attack_mode"]	= instrument.psg_envelope_attack_mode
			dict_instr["duty"]						= instrument.duty
			dict_instr["noise_shift_clock_freq"]	= instrument.noise_shift_clock_freq
			dict_instr["noise_counter_width"]		= instrument.noise_counter_width
			dict_instr["noise_dividing_ratio"]		= instrument.noise_dividing_ratio
			dict_instr["midi_mapping"]				= instrument.midi_mapping
			instruments_list.append(dict_instr)

		data_to_dump = dict()
		data_to_dump["curr_inst_id"] = self.curr_instr_id
		data_to_dump["last_sample_path"] = self.last_sample_path
		data_to_dump["instruments"] = instruments_list

		json.dump(data_to_dump, file)
		file.close()

	def file_save_as(self, *args):
		print ("file_save_as")
		#Open a file dialog, set the instrument file variable to be the returned file path
		if self.instrument_file_curr == None or len(self.instrument_file_curr) == 0:
			instrument_file_curr = filedialog.asksaveasfilename(filetypes=[("Instrument List (.json)", "*.json")], defaultextension="json", initialdir=os.getcwd())
		else:
			folder, file = os.path.split(self.instrument_file_curr)
			instrument_file_curr = filedialog.asksaveasfilename(filetypes=[("Instrument List (.json)", "*.json")], defaultextension="json", initialfile=file, initialdir = folder)


		#If the window is cancelled, it will return an empty string. If this is happens, don't update anything
		if len(instrument_file_curr) == 0:
			return

		self.instrument_file_curr = instrument_file_curr

		#Update the title
		self.title = "Instrument Creator - " + os.path.split(self.instrument_file_curr)[-1]
		self.root.title(self.title)

		#Save the file data
		self.file_save()

	def file_exit(self, *args):
		print ("file_exit")
		#If the file has been changed (we know by checking the window title for *)
		if self.title.endswith("*"):
			#Ask to save the file
			check = messagebox.askyesnocancel(title="Unsaved Changes", message="Instrument file has unsaved changes. Would you like to save the file?")
			if check == True:
				self.file_save()
				exit()
			elif check == False:
				exit()
		else:
			exit()

	def file_export(self, *args):
		print ("file_export")

		#Prompt user for file location
		if self.instrument_file_curr == None or len(self.instrument_file_curr) == 0:
			export_file_path = filedialog.askdirectory(initialdir=os.getcwd(), mustexist=True)
		else:
			folder, file = os.path.split(self.instrument_file_curr)
			file = os.path.splitext(file)[0] + ".bin"
			export_file_path = filedialog.askdirectory(initialdir=folder, mustexist=True)

		#If file path is empty, cancel
		if len(export_file_path) == 0:
			return

		#Save file
		InstrumentExporter.SaveFile(export_file_path, self.instruments)

	def help_about(self, *args):
		print ("help_about")
		messagebox.showinfo(title="About Instrument Creator", message="Instrument Creator\nMade by: FlannyH\n\nThis tool is meant to be used for my Game Boy Advance Music Engine, to easily create instrument files. It exports directly to binary files, ready to be imported in the engine.")

	def press_new_instrument(self):
		print ("press_new_instrument")
		#Enforce instrument limit
		if len(self.instruments) > 127:
			print ("Too many instruments!, delete some")
			return

		#Create new instrument and add it to the list
		new_instrument = Instrument()
		self.curr_instr_id = len(self.instruments)
		self.instruments.append(new_instrument)
		self.update_ui_elements()

	def press_remove_instrument(self):
		print ("press_remove_instrument")

		#Remove the current instrument
		self.instruments.remove(self.instruments[self.curr_instr_id])

		#Go to the first valid instrument before the one we just deleted
		while self.curr_instr_id >= len(self.instruments):
			self.curr_instr_id -= 1

		#If there's still instruments left
		if len(self.instruments) > 0:
			self.update_ui_elements()
		else:
			#Clear instruments list, and create a new one
			self.instruments = list()
			self.instruments.append(Instrument())
			self.update_ui_elements()

	def update_ui_elements(self, *args):
		print ("update_ui_elements")
		#Update names combobox
		names = list()
		i = 0
		for instrument in self.instruments:
			names.append(f"${hex(i)[2:].zfill(2).upper()} - {instrument.name}")
			i += 1
		self.combobox_instrument_list['values'] = names

		#Update widget variables
		instr = self.instruments[self.curr_instr_id]
		self.combobox_instrument_list					.set(names[self.curr_instr_id])
		self.instrument_name_curr						.set(instr.name)
		self.instrument_attack							.set(instr.attack)
		self.instrument_decay							.set(instr.decay)
		self.instrument_sustain							.set(instr.sustain)
		self.instrument_release							.set(instr.release)
		self.instrument_type_curr						.set(self.combobox_instrument_type['values'][instr.type])
		self.instrument_sample_curr						.set(instr.sample_source)
		self.instrument_loop_start						.set(instr.loop_start)
		self.instrument_loop_enable						.set(instr.loop_enable)
		self.instrument_length_curr						.set(instr.psg_length)
		self.instrument_psg_envelope_volume_curr		.set(instr.psg_envelope_volume)
		self.instrument_psg_envelope_speed_curr			.set(instr.psg_envelope_speed)
		self.instrument_psg_envelope_attack_mode_curr	.set(instr.psg_envelope_attack_mode)
		self.instrument_duty							.set(self.combobox_psg_duty['values'][instr.duty])
		self.instrument_noise_shift_clock_freq			.set(instr.noise_shift_clock_freq)
		self.instrument_noise_counter_width				.set(instr.noise_counter_width)
		self.instrument_noise_dividing_ratio			.set(instr.noise_dividing_ratio)
		self.instrument_midi_mapping					.set(instr.midi_mapping)

		#Hide all widgets
		for widget in self.pulse_widgets:
			widget.grid_remove()
		for widget in self.wave_widgets:
			widget.grid_remove()
		for widget in self.noise_widgets:
			widget.grid_remove()
		for widget in self.sample_widgets:
			widget.grid_remove()

		#Show the ones we want
		widget_lists = [self.sample_widgets, self.pulse_widgets, self.pulse_widgets, self.wave_widgets, self.noise_widgets]
		for widget in widget_lists[instr.type]:
			widget.grid()
		
	def change_instrument(self, *args):
		print ("change_instrument")
		self.curr_instr_id = self.combobox_instrument_list.current()
		self.update_ui_elements()
	
	def press_preview(self):
		print ("press_preview")
		
	def press_sample_source(self):
		print ("press_sample_source")

		print (self.last_sample_path)

		if self.last_sample_path:
			initial_dir = self.last_sample_path
		else:
			initial_dir = os.getcwd()

		file_to_put = filedialog.askopenfilename(filetypes=[("Sample", "*.wav")], multiple=False, initialdir=initial_dir)

		if len(file_to_put) > 0:
			self.instrument_sample_curr.set(file_to_put)
			initial_dir, _ = os.path.split(file_to_put)
			self.last_sample_path = initial_dir
		
		self.apply_instrument_values()
		self.update_ui_elements()

	def apply_instrument_values(self, *args):
		print ("apply_instrument_values")
		if not self.title.endswith("*"):
			self.title += "*"
			self.root.title(self.title)

		self.instruments[self.curr_instr_id].name 									= self.entry_name.get()
		self.instruments[self.curr_instr_id].attack 								= self.instrument_attack.get()
		self.instruments[self.curr_instr_id].decay 									= self.instrument_decay.get()
		self.instruments[self.curr_instr_id].sustain 								= self.instrument_sustain.get()
		self.instruments[self.curr_instr_id].release 								= self.instrument_release.get()
		self.instruments[self.curr_instr_id].type									= self.combobox_instrument_type.current()
		self.instruments[self.curr_instr_id].sample_source 							= self.entry_sample_source.get()
		self.instruments[self.curr_instr_id].loop_start 							= self.spinbox_loop_start.get()
		self.instruments[self.curr_instr_id].loop_enable 							= self.instrument_loop_enable.get()
		self.instruments[self.curr_instr_id].psg_length			 					= self.spinbox_psg_length.get()
		self.instruments[self.curr_instr_id].psg_envelope_volume 					= self.instrument_psg_envelope_volume_curr.get()
		self.instruments[self.curr_instr_id].psg_envelope_speed 					= self.instrument_psg_envelope_speed_curr.get()
		self.instruments[self.curr_instr_id].psg_envelope_attack_mode 				= self.instrument_psg_envelope_attack_mode_curr.get()
		self.instruments[self.curr_instr_id].duty 									= self.combobox_psg_duty.current()
		self.instruments[self.curr_instr_id].noise_shift_clock_freq					= self.instrument_noise_shift_clock_freq.get()	
		self.instruments[self.curr_instr_id].noise_counter_width					= self.instrument_noise_counter_width.get()
		self.instruments[self.curr_instr_id].noise_dividing_ratio					= self.instrument_noise_dividing_ratio.get()
		self.instruments[self.curr_instr_id].midi_mapping					= self.instrument_midi_mapping.get()
		self.update_ui_elements()
		
	def fix_values(self, *args):
		print ("fix_values")
		self.instrument_psg_envelope_volume_curr.set(str(int(float(self.instrument_psg_envelope_volume_curr.get()))))
		self.instrument_psg_envelope_speed_curr.set(str(int(float(self.instrument_psg_envelope_speed_curr.get()))))
		self.apply_instrument_values()
		self.update_ui_elements()
		
if __name__ == "__main__":
	root = Tk()
	InstrumentEditor(root)
	root.mainloop()