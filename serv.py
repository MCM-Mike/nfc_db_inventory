import json
import base64
import warnings
from threading import Thread, Event
from random import random
from time import sleep

from flask import Flask, Response, request, render_template, g
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from smartcard.CardConnectionObserver import ConsoleCardConnectionObserver
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString, toBytes

from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.util import toHexString, toBytes
from smartcard.CardConnection import CardConnection

from models import NfcTag, MYSQL_CONN_STR, db
from nfc import CardObserver


app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_CONN_STR


with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=sa_exc.SAWarning)
    db.init_app(app)


# from https://pyscard.sourceforge.io/user-guide.html#the-answer-to-reset-atr
# a simple card observer that tries to select DF_TELECOM on an inserted card
class selectDFTELECOMObserver(CardObserver):
    """A simple card observer that is notified
    when cards are inserted/removed from the system and
    prints the list of cards
    """

    def __init__(self):
        self.observer = ConsoleCardConnectionObserver()

    def update(self, observable, actions):
        print('in update')
        (addedcards, removedcards) = actions
        print(addedcards, removedcards)
        for card in addedcards:
            print("+Inserted: ", toHexString(card.atr))
            card.connection = card.createConnection()
            card.connection.connect()
            card.connection.addObserver(self.observer)

            # this byte string differs for diffent tags
            command = toBytes('FF CA 00 00 00')
            response, sw1, sw2 = card.connection.transmit(command)
            uid = toHexString(response).replace(' ','')
            print('card uid = ', uid)

            with app.app_context():

                tag = NfcTag.query.get(uid)

                if tag is None:
                    tag = NfcTag(tag_id=uid)

                description = '' if tag.description is None else tag.description
                date_purchased = '' if tag.date_purchased is None else tag.date_purchased.strftime("%Y-%m-%d")
                last_time_used = '' if tag.last_time_used is None else tag.last_time_used.strftime("%Y-%m-%d")
                socketio.emit('newnumber', {'tag_id': uid, 'description': description, 'date_purchased': date_purchased, 'last_time_used': last_time_used}, namespace='/test')

        for card in removedcards:
            print("-Removed: ", toHexString(card.atr))


class MyCardObserver():
    def __init__(self):
        self._cardmonitor = CardMonitor()
        self._selectobserver = selectDFTELECOMObserver()

    def start_observe(self):
        print("observer started")
        #socketio.emit('newnumber', {'number': 'start'}, namespace='/test')
        self._cardmonitor.addObserver(self._selectobserver)

    def stop_observe(self):
        self._cardmonitor.deleteObserver(self._selectobserver)


#turn the flask app into a socketio app
socketio = SocketIO(app)

#nfc reader Thread
thread = Thread()
thread_stop_event = Event()

mycard_observer = MyCardObserver()

class RandomThread(Thread):
    def __init__(self):
        self.delay = 1
        super(RandomThread, self).__init__()

    def randomNumberGenerator(self):
        """
        Generate a random number every 1 second and emit to a socketio instance (broadcast)
        Ideally to be run in a separate thread?
        """
        mycard_observer.start_observe()


    def run(self):
        self.randomNumberGenerator()


@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread")
        thread = RandomThread()
        thread.start()


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')
    #mycard_observer.stop_observe()


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


@app.route('/', methods=['POST', 'GET'])
def edit_nfctag():

    cardtype = AnyCardType()
    cardrequest = CardRequest( timeout=1, cardType=cardtype )

    try:
        cardservice = cardrequest.waitforcard()
    except:
        return render_template('nfctag_data.html', message='Please put a tag on the reader.')

    stat = cardservice.connection.connect()

    command = toBytes('FF CA 00 00 00')
    response, sw1, sw2 = cardservice.connection.transmit(command)
    uid = toHexString(response).replace(' ','')

    message = ''

    if request.method == 'POST':
        #message = 'inside post'

        tag = NfcTag.query.get(uid)

        if tag is None:
            message = 'inside get tag is none'
            tag = NfcTag(tag_id=uid)
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

    #elif request.method == 'GET':

        ##message = 'inside get'

        #tag = NfcTag.query.get(uid)

        #if tag is None:
            #message = 'inside get tag is none'
            #tag = NfcTag(tag_id=uid)
            #try:
                #db.session.add(tag)
                #db.session.commit()
            #except Exception as e:
                #message = "Failed to add a tag: {}".format(str(e))
            #else:
                #message = "New tag has been added successfully"
        #else:
            #message = "Tag data has been read successfully"

    description = '' if tag.description is None else tag.description
    return render_template('nfctag_data.html', tag_id=tag.tag_id, description=description, date_purchased=tag.date_purchased, last_time_used=tag.last_time_used, message=message)


if __name__ == '__main__':
    def set_wing_ide_debugger():
        import os
        if 'WINGDB_ACTIVE' in os.environ:
            app.debug = False

    set_wing_ide_debugger()
    app.run(port=5000)
