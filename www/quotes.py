import flask
import math
from www import server
from www import login
from common import utils

QUOTES_PER_PAGE = 25

@server.app.route('/quotes/')
@server.app.route('/quotes/<int:page>')
@login.with_session
@utils.with_postgres
def quotes(conn, cur, session, page = 1):
	cur.execute("SELECT COUNT(*) FROM quotes WHERE deleted = FALSE")
	count, = next(cur)
	pages = math.ceil(count / QUOTES_PER_PAGE)

	page = max(0, min(page - 1, pages))

	cur.execute("""
		SELECT qid, quote, attrib_name, attrib_date
		FROM quotes
		WHERE NOT deleted
		ORDER BY qid DESC
		OFFSET %s
		LIMIT %s
	""", (page * QUOTES_PER_PAGE, QUOTES_PER_PAGE))

	return flask.render_template('quotes.html', session=session, page=page, quotes=list(cur), pages=pages)
