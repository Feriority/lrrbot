import os
import datetime
import subprocess

import flask
import pytz
import jinja2.utils

from common import config
from common.utils import cache
from www import login

def error_page(message):
	return flask.render_template("error.html", message=message, session=login.load_session(include_url=False))

def timestamp(ts):
	"""
	Outputs a given time (either unix timestamp or datetime instance) as a human-readable time
	and includes tags so that common.js will convert the time on page-load to the user's
	timezone and preferred date/time format.
	"""
	if isinstance(ts, (int, float)):
		ts = datetime.datetime.fromtimestamp(ts, tz=pytz.utc)
	elif ts.tzinfo is None:
		ts = ts.replace(tzinfo=datetime.timezone.utc)
	ts = ts.astimezone(config.config['timezone'])
	return flask.Markup("<span class=\"timestamp\" data-timestamp=\"{}\">{:%A, %d %B, %Y %H:%M:%S %Z}</span>".format(ts.timestamp(), ts))

@cache(period=None, params=[0])
def static_url(filename):
	baseurl = flask.url_for("static", filename=filename)
	revision = subprocess.check_output([
		'git', 'log', '-n', '1', '--pretty=format:%h', '--',
		os.path.join('www', 'static', filename)]).decode()
	return "{}?_={}".format(baseurl, revision)

# Add a "last" to get the previous value returned, to complement the existing
# "current" prop which gets the upcoming value.
class CyclerExt(jinja2.utils.Cycler):
	@property
	def last(self):
		# self.pos is always positive or zero, so this will wrap cleanly
		return self.items[self.pos - 1]
