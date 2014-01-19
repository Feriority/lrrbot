import urllib.request, urllib.parse
import json
import time
from config import config

def get_info(username=None):
	"""
	Get the Twitch info for a particular user or channel.

	Defaults to the stream channel if not otherwise specified.

	For response object structure, see:
	https://github.com/justintv/Twitch-API/blob/master/v3_resources/channels.md#example-response

	May throw exceptions on network/Twitch error.
	"""
	if username is None:
		username = config['channel']
	res = urllib.request.urlopen("https://api.twitch.tv/kraken/channels/%s" % username).read().decode()
	return json.loads(res)

def get_game(name, all=False):
	"""
	Get the game information for a particular game.

	For response object structure, see:
	https://github.com/justintv/Twitch-API/blob/master/v3_resources/search.md#example-response-1	

	May throw exceptions on network/Twitch error.
	"""
	search_opts = {
		'query': name,
		'type': 'suggest',
		'live': 'false',
	}
	res = urllib.request.urlopen("https://api.twitch.tv/kraken/search/games?" + urllib.parse.urlencode(search_opts)).read().decode()
	res = json.loads(res)
	if all:
		return res['games']
	else:
		for game in res['games']:
			if game['name'] == name:
				return game
		return None

def get_game_playing(username=None):
	"""
	Get the game information for the game the stream is currently playing
	"""
	channel_data = get_info(username)
	if channel_data['game'] is not None:
		return get_game(name=channel_data['game'])
	return None
