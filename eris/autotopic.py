import asyncio
import dateutil
import datetime
import sqlalchemy
import textwrap

from common.config import config
from common import rpc
from common import googlecalendar
from common import time
from common import utils
from common import twitch

import logging
log = logging.getLogger('eris.autotopic')

MAX_TOPIC_LENGTH = 1024

class Autotopic:
	def __init__(self, eris, signals, engine, metadata):
		self.eris = eris
		self.signals = signals
		self.engine = engine
		self.metadata = metadata

		self.timer_scheduled = False
		self.signals.signal('ready').connect(self.schedule_timer)

	# Simplified copy of `lrrbot.commands.misc.uptime_msg`.
	def uptime_msg(self):
		stream_info = twitch.get_info()
		if stream_info and stream_info.get("stream_created_at"):
			start = dateutil.parser.parse(stream_info["stream_created_at"])
			now = datetime.datetime.now(datetime.timezone.utc)
			return "The stream has been live for %s." % time.nice_duration(now - start, 0)
		elif stream_info and stream_info.get('live'):
			return "Twitch won't tell me when the stream went live."
		else:
			return "The stream is not live."

	@utils.swallow_errors
	async def update_topic(self):
		channel = self.eris.get_server(config['discord_serverid']).default_channel
		header = await rpc.bot.get_header_info()
		messages = []

		if header['is_live']:
			shows = self.metadata.tables["shows"]
			games = self.metadata.tables["games"]
			game_per_show_data = self.metadata.tables["game_per_show_data"]
			with self.engine.begin() as conn:
				if header.get('current_game'):
					game = conn.execute(sqlalchemy.select([
						sqlalchemy.func.coalesce(game_per_show_data.c.display_name, games.c.name)
					]).select_from(
						games.outerjoin(game_per_show_data,
							(game_per_show_data.c.game_id == games.c.id) &
								(game_per_show_data.c.show_id == header['current_show']['id']))
					).where(games.c.id == header['current_game']['id'])).first()
					if game is not None:
						game, = game
				else:
					game = None
				
				if header.get('current_show'):
					show = conn.execute(sqlalchemy.select([shows.c.name])
						.where(shows.c.id == header['current_show']['id'])
						.where(shows.c.string_id != "")).first()
					if show is not None:
						show, = show
				else:
					show = None

			if game and show:
				messages.append("Now live: %s on %s." % (game, show))
			elif game:
				messages.append("Now live: %s." % game)
			elif show:
				messages.append("Now live: %s." % show)
			messages.append(self.uptime_msg())
		else:
			now = datetime.datetime.now(datetime.timezone.utc)
			events = googlecalendar.get_next_event(googlecalendar.CALENDAR_LRL, after=now)
			for event in events:
				if event['start'] > now:
					message = "In %s: " % time.nice_duration(event['start'] - now, 1)
				else:
					message = "%s ago: " % time.nice_duration(now - event['start'], 1)
				message += event['title']
				if event['description'] is not None:
					message += " (%s)" % (textwrap.shorten(googlecalendar.process_description(event['description']), 200))
				message += " at " + event['start'].astimezone(config['timezone']).strftime(googlecalendar.DISPLAY_FORMAT)
				message += "."
				messages.append(message)
		if header.get('advice'):
			messages.append(header['advice'])
		await self.eris.edit_channel(channel, topic=textwrap.shorten(" ".join(messages), MAX_TOPIC_LENGTH))


	def schedule_update_topic(self):
		asyncio.ensure_future(self.update_topic(), loop=self.eris.loop).add_done_callback(utils.check_exception)
		self.eris.loop.call_later(60, self.schedule_update_topic)

	def schedule_timer(self, eris):
		if not self.timer_scheduled:
			self.timer_scheduled = True
			self.schedule_update_topic()
