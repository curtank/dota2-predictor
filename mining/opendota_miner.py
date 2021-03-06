#!/usr/bin/env python

""" This module mines from opendota public API given a list of games
The output is in the format specified in mining_headers.csv
"""

from __future__ import print_function
import csv
import json
import sys
import urllib
import time

OPENDOTA_BASE_URL = "https://api.opendota.com/api/matches/"
REQUEST_TIMEOUT = 0.3
MAX_RETRIES = 10

class OpendotaMiner(object):
	""" Sends HTTP requests to opendota, parses the JSON that comes as a
	response and saves data regarding the average MMR of the games

	Keyword arguments:
	games_list -- list of match IDs to be processed
	output_file -- output file handle
	"""

	def __init__(self, list_of_games, output_file_handle):
		self.games_list = list_of_games
		self.output_file = output_file_handle

	def process_request(self, game, retries):
		""" Gets the data through HTTP request and writes it to file for
		a single game

		game -- match ID to be processed
		retries -- number of retries until proceeding to the next request
		"""

		url = OPENDOTA_BASE_URL + str(game)
		response = urllib.urlopen(url)

		try:
			game_json = json.load(response)
		except ValueError:
			print("Error parsing JSON at game " + str(game))
			return

		if "error" in game_json:
			print("Response error at game " + str(game))
			if retries < MAX_RETRIES:
				time.sleep(REQUEST_TIMEOUT)
				self.process_request(game, retries + 1)
			return

		if "radiant_win" not in game_json:
			print("JSON is corrupted, skipping " + str(game))
			return
		else:
			radiant_win = game_json["radiant_win"]

		csv_entry = str(game) + ","

		players_list = game_json["players"]
		mmr_shown = 0
		mmr_sum = 0

		for i in range(10):
			try:
				player = players_list[i]
			except IndexError:
				print("Index error at game " + str(game))
				return

			csv_entry += str(player["hero_id"]) + ","

			if player["solo_competitive_rank"]:
				mmr_shown += 1
				mmr_sum += int(player["solo_competitive_rank"])

		csv_entry += str(mmr_shown) + ","
		mmr_avg = int(mmr_sum / mmr_shown) if mmr_shown > 0 else -1
		csv_entry += str(mmr_avg) + ","
		csv_entry += "1\n" if radiant_win else "0\n"
		self.output_file.write(csv_entry)

	def run(self):
		""" Schedules HTTP requests, one per REQUEST_TIMEOUT seconds """
		games_count = len(self.games_list)
		start_time = time.time()
		for i in range(games_count):
			self.process_request(self.games_list[i], 0)

			if i % 10 == 9:
				elapsed_time = time.time() - start_time
				print("Processed %d games in %.2f seconds." % (i + 1, elapsed_time))

			time.sleep(REQUEST_TIMEOUT)


def main():
	""" Main function """

	if len(sys.argv) < 4:
		sys.exit("Usage: %s <input_file> <output_file> <number_of_games>" % sys.argv[0])

	try:
		in_file = open(sys.argv[1], "rt")
	except IOError:
		sys.exit("Invalid input file")

	try:
		out_file = open(sys.argv[2], "a")
	except IOError:
		sys.exit("Invalid output file")

	try:
		games_number = int(sys.argv[3])
	except ValueError:
		sys.exit("Invalid number of games")

	csv_reader = csv.reader(in_file, delimiter=",")
	full_list = list(csv_reader)

	games_list = [full_list[j][0] for j in range(games_number)]
	miner = OpendotaMiner(games_list, out_file)
	miner.run()

	in_file.close()
	out_file.close()

if __name__ == "__main__":
	main()
