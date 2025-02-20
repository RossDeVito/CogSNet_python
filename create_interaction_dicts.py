"""
Reads in phone interaction from NetSenseBehavioralDataWS.csv and saves to dicts
	which will then be used to create models
"""

import os
import pickle
import time
import datetime
from collections import defaultdict

import pandas as pd

def add_interaction_old(interaction, edge_dict, interaction_dict):
	"""
	Given a named tuple of a NetSense data phone record with unix_time added
		adds record to interaction and edge dicts
	"""
	edge_dict[interaction.id1].add(interaction.id2)
	edge_dict[interaction.id2].add(interaction.id1)

	interaction_dict[interaction.id1][interaction.id2].append([
		interaction.event_type,		# 0 for call, 1 for message
		interaction.event_length,	# minutes/message size
		interaction.unix_time
	])
	interaction_dict[interaction.id2][interaction.id1].append([
		interaction.event_type,		# 0 for call, 1 for message
		interaction.event_length,  	# minutes/message size
		interaction.unix_time
	])


def add_interaction(interaction, edge_dict, interaction_dict):
	"""
	Given a named tuple of a NetSense data phone record with unix_time added
		adds record to interaction and edge dicts
	"""
	if interaction.resp_id == interaction.id1:
		inter_with_id = interaction.id2
	elif interaction.resp_id == interaction.id2:
		inter_with_id = interaction.id1
	else:
		raise SystemExit("Respondant id not in event info")

	edge_dict[interaction.id1].add(interaction.id2)
	edge_dict[interaction.id2].add(interaction.id1)

	interaction_dict[interaction.resp_id][inter_with_id].append([
		interaction.event_type,		# 0 for call, 1 for message
		interaction.event_length,  # minutes/message size
		interaction.unix_time
	])


if __name__ == "__main__":
	# phone_data = pd.read_csv(os.path.join("data", "reality_commons_telcodata.txt"),
	# 							sep=';',
	# 							names=['datetime', 'resp_id', 
	# 									'id1', 'id2', 
	# 									'event_type', 'event_length'])
	phone_data = pd.read_csv(os.path.join("data", "nethealth_data", 
										   "nethealth_telcodata.txt"),
								sep=';',
								names=['datetime', 'resp_id', 
										'id1', 'id2', 
										'event_type', 'event_length'])

	print("Read telcodata")
	print("Preparing data")

	# drop row resulting from terminating -1 in file
	phone_data = phone_data.dropna()

	print("\tdropped na")

	# ids and event types to ints
	phone_data.id1 = phone_data.id1.astype(int)
	phone_data.id2 = phone_data.id2.astype(int)
	phone_data.event_type = phone_data.event_type.astype(int)
	phone_data.event_length = phone_data.event_length.astype(int)

	print("\tconverted to ints")

	# add unix time and remove then unneeded DateList
	phone_data['unix_time'] = phone_data.datetime.apply(lambda t: 
		time.mktime(datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S").timetuple())).astype(int)
	phone_data = phone_data.drop("datetime", axis=1)

	print("\tconverted to datetime")
	
	# dict that will map from a user id to the set of all user ids it will
	# have an edge with
	edge_dict = defaultdict(set)

	# dict that will map two user ids (an edge) to a list of all interactions
	# between them. Order of two user ids will always be (lower_num, greater_num)
	interaction_dict = defaultdict(lambda: defaultdict(list))

	print("Adding interactions")
	n = len(phone_data)
	i = 1

	# for each row, add interaction to dicts
	for interaction in phone_data.itertuples(index=False):
		print("\t{} / {}".format(i, n))
		i += 1
		add_interaction(interaction, edge_dict, interaction_dict)

	print("Finished adding interactions")

	edge_dict = dict(edge_dict)
	interaction_dict = dict(interaction_dict)

	for key in interaction_dict.keys():
		for edge_with_key in interaction_dict[key].keys():
			interaction_dict[key][edge_with_key] = pd.DataFrame(
					interaction_dict[key][edge_with_key]).values
		interaction_dict[key] = dict(interaction_dict[key])

	with open(os.path.join("data", "nethealth_edge_dict.pkl"), 'wb') as pkl:
		pickle.dump(edge_dict, pkl, protocol=pickle.HIGHEST_PROTOCOL)

	with open(os.path.join("data", "nethealth_interaction_dict.pkl"), 'wb') as pkl:
		pickle.dump(interaction_dict, pkl, protocol=pickle.HIGHEST_PROTOCOL)
