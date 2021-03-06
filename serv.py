"""
Implement flask service with a thread for monitoring NFC reader.

Resources:
https://www.shanelynn.ie/asynchronous-updates-to-a-webpage-with-flask-and-socket-io/
https://pyscard.sourceforge.io/user-guide.html
"""

import json
import base64
import warnings
from threading import Thread, Event
from random import random
from time import sleep

from flask import Flask, Response, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, InvalidRequestError

from models import NfcTag, MYSQL_CONN_STR, db
from card_monitor import MyCardMonitor, CardMonitorThread


app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_CONN_STR


with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=sa_exc.SAWarning)
    db.init_app(app)


#turn the flask app into a socketio app
socketio = SocketIO(app)

#nfc reader Thread
thread = Thread()
thread_stop_event = Event()

mycard_monitor = MyCardMonitor(socketio, app)


@socketio.on('connect', namespace='/nfc')
def nfc_connect():
    # need visibility of the global thread object
    global thread
    print('Client connected')

    if not thread.isAlive():
        print("Starting Thread")
        thread = CardMonitorThread(mycard_monitor)
        thread.start()
        print('thread is alive', thread.isAlive())


@socketio.on('disconnect', namespace='/nfc')
def nfc_disconnect():
    print('Client disconnected')
    global thread
    # this should be enough to stop the thread
    mycard_monitor.stop_observe()
    print('thread is alive', thread.isAlive())
    #thread._stop()


@app.route('/get_status')
def get_status():
    ##header("Content-type: application/json")
    cardtype = AnyCardType()
    cardrequest = CardRequest( timeout=1, cardType=cardtype )
    try:
        cardservice = cardrequest.waitforcard()
    except:
        resultdict = {
            'status':'inactive'
        }
        return json.dumps(resultdict)

    resultdict = {
        'status':'active'
    }
    return Response(json.dumps(resultdict), mimetype='application/json')


@app.route('/', methods=['GET', 'POST'])
def edit_nfctag():

    if not mycard_monitor.has_card():
        return render_template('nfctag_data.html', message='Please put a tag on the reader.')

    if request.method == 'GET':
        # we show the html template here and the data will come from the nfc monitor thread
        return render_template('nfctag_data.html', message='Tag data is comming...')

    elif request.method == 'POST':

        tag_id = request.form['tag_id']
        tag = NfcTag.query.get(tag_id)

        if tag is None:
            tag = NfcTag(tag_id=tag_id)
            try:
                db.session.add(tag)
                db.session.commit()
            except Exception as e:
                message = "Failed to add a tag: {}".format(str(e))
            else:
                message = "New tag has been added successfully"

        for column, value in request.form.items():
            value = None if value == '' else value
            setattr(tag, column, value)

        db.session.commit()

        message = "The tag data has been updated successfully"

        description = '' if tag.description is None else tag.description
        return render_template('nfctag_data.html', tag_id=tag.tag_id, description=description, date_purchased=tag.date_purchased, last_time_used=tag.last_time_used, message=message)


if __name__ == '__main__':
    def set_wing_ide_debugger():
        import os
        if 'WINGDB_ACTIVE' in os.environ:
            app.debug = False

    set_wing_ide_debugger()
    app.run(port=5000)
