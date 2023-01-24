from flask import Flask, request, render_template
import os
import random
import redis
import socket
import sys
import logging
from datetime import datetime

# App Insights
# TODO: Import required libraries for App Insights
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

# Logging
logger = logging.getLogger('azure')
handler = AzureLogHandler(
    connection_string='InstrumentationKey=8c2baa4a-b152-4e5b-9c02-673ca52daad0')
logger.addHandler(handler)


# Metrics
exporter = AzureExporter(
    connection_string='InstrumentationKey=8c2baa4a-b152-4e5b-9c02-673ca52daad0'),

# Tracing
tracer = Tracer(
    exporter=exporter,
    sampler=ProbabilitySampler(1.0)
)

app = Flask(__name__)

# Requests
middleware = FlaskMiddleware(
    app,
    exporter=AzureExporter(
        connection_string="InstrumentationKey=8c2baa4a-b152-4e5b-9c02-673ca52daad0"),
    sampler=ProbabilitySampler(rate=1.0),
)

# Testing App Insights
# logger.warning('Before the span')
# with tracer.span(name='test'):
#     logger.warning('In the span')
# logger.warning('After the span')


# Load configurations from environment or config file
app.config.from_pyfile('config_file.cfg')

if ("VOTE1VALUE" in os.environ and os.environ['VOTE1VALUE']):
    button1 = os.environ['VOTE1VALUE']
else:
    button1 = app.config['VOTE1VALUE']

if ("VOTE2VALUE" in os.environ and os.environ['VOTE2VALUE']):
    button2 = os.environ['VOTE2VALUE']
else:
    button2 = app.config['VOTE2VALUE']

if ("TITLE" in os.environ and os.environ['TITLE']):
    title = os.environ['TITLE']
else:
    title = app.config['TITLE']

# Redis Connection
r = redis.Redis()

# Change title to host name to demo NLB
if app.config['SHOWHOST'] == "true":
    title = socket.gethostname()

# Init Redis
if not r.get(button1):
    r.set(button1, 0)
if not r.get(button2):
    r.set(button2, 0)


@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'GET':

        # Get current values
        vote1 = r.get(button1).decode('utf-8')
        print(vote1)
        # TODO: use tracer object to trace cat vote
        tracer.span(name=vote1)
        vote2 = r.get(button2).decode('utf-8')
        print(vote2)
        # TODO: use tracer object to trace dog vote
        tracer.span(name=vote2)

        # Return index with values
        return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

    elif request.method == 'POST':

        if request.form['vote'] == 'reset':

            # Empty table and return results
            r.set(button1, 0)
            r.set(button2, 0)
            vote1 = r.get(button1).decode('utf-8')
            properties = {'custom_dimensions': {'Cats Vote': vote1}}
            # TODO: use logger object to log cat vote

            logger.info('Cats Vote: %s', vote1, extra=properties)
            print('Cats Vote: %s', vote1, extra=properties)
            vote2 = r.get(button2).decode('utf-8')
            properties = {'custom_dimensions': {'Dogs Vote': vote2}}
            # TODO: use logger object to log dog vote

            logger.info('Dogs Vote: %s', vote2, extra=properties)
            print('Dogs Vote: %s', vote2, extra=properties)

            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

        else:

            # Insert vote result into DB
            vote = request.form['vote']
            r.incr(vote, 1)

            # Get current values
            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')

            # Return results
            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)


if __name__ == "__main__":
    # TODO: Use the statement below when running locally
    # app.run()
    # TODO: Use the statement below before deployment to VMSS
    app.run(host='0.0.0.0', threaded=True, debug=True)  # remote
