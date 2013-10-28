"""
Tools for dealing with a Macintosh resource fork.
"""
import struct
import StringIO
#from macfontextractor.resource_handlers import build_handler_for_type

RESOURCE_HEADER = (
		# From "Inside Macintosh: More Macintosh Toolbox", figure 1-12.
		">"		# Big-endian as per Motorola standard.
		"L"		# Resource data offset.
		"L"		# Resource map offset.
		"L"		# Resource data size.
		"L"		# Resource map size.
	)
RESOURCE_HEADER_SIZE = struct.calcsize(RESOURCE_HEADER)
assert RESOURCE_HEADER_SIZE == 16

RESOURCE_MAP = (
		# From "Inside Macintosh: More Macintosh Toolbox", figure 1-14.
		">"		# Big-endian as per Motorola standard.
		"16s"	# A copy of the resource header.
		"L"		# Handle to next resource map
		"H"		# File reference number
		"H"		# Resource fork attributes
		"H"		# Resource type list offset (from start of map)
		"H"		# Resource name list offset (from start of map)
		"H"		# zero-based index of the last type in the list.
	)
RESOURCE_MAP_SIZE = struct.calcsize(RESOURCE_MAP)
assert RESOURCE_MAP_SIZE == 30

RESOURCE_TYPE_ENTRY = (
		# From "Inside Macintosh: More Macintosh Toolbox", figure 1-15.
		">"		# Big-endian as per Motorola standard.
		"4s"	# The resource-type described in this entry.
		"H"		# zero-based index of the last resource of this type.
		"H"		# Resource reference list offset (from start of type list)
	)
RESOURCE_TYPE_ENTRY_SIZE = struct.calcsize(RESOURCE_TYPE_ENTRY)
assert RESOURCE_TYPE_ENTRY_SIZE == 8

RESOURCE_REFERENCE_ENTRY = (
		# From "Inside Macintosh: More Macintosh Toolbox", figure 1-16.
		">"		# Big-endian as per Motorola standard.
		"h"		# Resource ID.
		"h"		# Resource name offset (from start of name list, -1 is no name)
		"B"		# Resource attributes
		"B"		# Resource data offset (byte 1 of 3, from resource data start)
		"H"		# Resource data offset (bytes 2-3 of 3)
		"L"		# Resource handle
	)
RESOURCE_REFERENCE_ENTRY_SIZE = struct.calcsize(RESOURCE_REFERENCE_ENTRY)
assert RESOURCE_REFERENCE_ENTRY_SIZE == 12


class ResourceFork(object):
	def __init__(self, handle):
		self.handle = handle

		# Read the header and find the map and data.
		raw_header = handle.read(RESOURCE_HEADER_SIZE)
		data_offset, map_offset, data_size, map_size = struct.unpack(
				RESOURCE_HEADER, raw_header)

		handle.seek(data_offset)
		self.raw_resource_data = handle.read(data_size)
		handle.seek(map_offset)
		raw_map = handle.read(map_size)

		(_, _next_map_handle, _file_reference, self.flags,
				self.type_list_start, self.name_list_start,
				self.last_type_index) = struct.unpack(RESOURCE_MAP,
						raw_map[:RESOURCE_MAP_SIZE])

		# type_list_start is supposed to be the offset from the beginning of
		# the type-map, but the type-map is 30 bytes long and type_list_start
		# is frequently set to 28 bytes. What the hell is going on?
		real_type_list_start = max(self.type_list_start, RESOURCE_MAP_SIZE)

		self.resource_types = {}
		while len(self.resource_types) < self.last_type_index + 1:
			entry_start = (real_type_list_start
					+ len(self.resource_types) * RESOURCE_TYPE_ENTRY_SIZE)
			entry_end = entry_start + RESOURCE_TYPE_ENTRY_SIZE
			raw_type_entry = raw_map[entry_start:entry_end]

			type_name, resource_refs = self._read_type_entry(raw_map,
					raw_type_entry)
			self.resource_types[type_name] = resource_refs

	def _read_type_entry(self, raw_map, raw_type_entry):
		type_name, last_ref_index, ref_list_start = struct.unpack(
				RESOURCE_TYPE_ENTRY, raw_type_entry)

		resource_refs = {}

		while len(resource_refs) < last_ref_index + 1:
			ref_start = (self.type_list_start + ref_list_start 
					+ len(resource_refs) * RESOURCE_REFERENCE_ENTRY_SIZE)
			ref_end = ref_start + RESOURCE_REFERENCE_ENTRY_SIZE
			raw_ref = raw_map[ref_start:ref_end]
			res_id, res_name, res_attributes, res_data = self._read_res_ref(
					raw_map, raw_ref)
			resource_refs[res_id] = (res_name, res_attributes, res_data)

		return type_name, resource_refs

	def _read_res_ref(self, raw_map, raw_ref):
		(res_id, res_name_start, res_attributes, res_data_1, res_data_23,
				res_handle) = struct.unpack(RESOURCE_REFERENCE_ENTRY, raw_ref)

		if res_name_start == -1:
			res_name = None
		else: 
			# Names are stored as:
			#  1 byte - name length
			#  n bytes - actual name
			res_name_length_offset = self.name_list_start+res_name_start
			res_name_length = ord(raw_map[res_name_length_offset])
			res_name_start = res_name_length_offset + 1
			res_name = raw_map[res_name_start:res_name_start+res_name_length]


		# Data is stored as:
		#  4 bytes - data length
		#  n bytes - actual data
		res_data_length_start = (res_data_1 << 16) + res_data_23
		res_data_length_end = res_data_length_start + 4
		raw_length = self.raw_resource_data[
				res_data_length_start:res_data_length_end
			]
		res_data_length = struct.unpack(">L", raw_length)[0]
		res_data = self.raw_resource_data[
				res_data_length_end:res_data_length_end+res_data_length
			]

		return res_id, res_name, res_attributes, res_data

	def __repr__(self):
		return "<ResourceFork with %d types>" % (
				self.last_type_index + 1,
			)

	def get_resource_types(self):
		return sorted(self.resource_types.keys())

	def get_resource(self, type, id):
		res_name, res_attributes, res_data = \
				self.resource_types[type][id]

		s = StringIO.StringIO(res_data)
		s.tag = type
		s.size = len(res_data)
		s.rid = id
		return s
#		return build_handler_for_type(type, self, id, res_name, res_data)

	def get_resources_by_type(self, type):
		return [self.get_resource(type, id) 
				for id in self.resource_types[type].keys()]

	def get_all_resources(self):
		r = {}
		for i in self.get_resource_types():
			r[i] = self.get_resources_by_type(i)
		return r
