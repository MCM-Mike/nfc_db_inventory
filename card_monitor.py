from threading import Thread

from smartcard.CardConnectionObserver import ConsoleCardConnectionObserver
from smartcard.CardMonitoring import CardMonitor, CardObserver

from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.util import toHexString, toBytes
from smartcard.CardConnection import CardConnection

from models import NfcTag


class MyCardObserver(CardObserver):
    """A simple card observer that is notified
    when cards are inserted/removed from the system and
    prints the list of cards
    """

    def __init__(self, socketio, flask_app):
        self._observer = ConsoleCardConnectionObserver()
        self._socketio = socketio
        self._flask_app = flask_app

    def update(self, observable, actions):
        print('in update')
        (addedcards, removedcards) = actions
        print(addedcards, removedcards)
        for card in addedcards:
            print("+Inserted: ", toHexString(card.atr))
            card.connection = card.createConnection()
            card.connection.connect()
            card.connection.addObserver(self._observer)

            # this byte string differs for diffent tags
            command = toBytes('FF CA 00 00 00')
            response, sw1, sw2 = card.connection.transmit(command)
            uid = toHexString(response).replace(' ','')
            print('card uid = ', uid)

            with self._flask_app.app_context():

                tag = NfcTag.query.get(uid)

                if tag is None:
                    tag = NfcTag(tag_id=uid)

                description = '' if tag.description is None else tag.description
                date_purchased = '' if tag.date_purchased is None else tag.date_purchased.strftime("%Y-%m-%d")
                last_time_used = '' if tag.last_time_used is None else tag.last_time_used.strftime("%Y-%m-%d")
                self._socketio.emit('newnumber', {'tag_id': uid, 'description': description, 'date_purchased': date_purchased, 'last_time_used': last_time_used}, namespace='/test')

        for card in removedcards:
            print("-Removed: ", toHexString(card.atr))


class MyCardMonitor():
    def __init__(self, socketio, flask_app):
        self._cardmonitor = CardMonitor()
        self._selectobserver = MyCardObserver(socketio, flask_app)

    def start_observe(self):
        print("observer started")
        #socketio.emit('newnumber', {'number': 'start'}, namespace='/test')
        self._cardmonitor.addObserver(self._selectobserver)

    def stop_observe(self):
        self._cardmonitor.deleteObserver(self._selectobserver)


class CardMonitorThread(Thread):
    def __init__(self, mycard_monitor):
        self._mycard_monitor = mycard_monitor
        super(CardMonitorThread, self).__init__()

    def _start_card_monitor(self):
        self._mycard_monitor.start_observe()

    def run(self):
        self._start_card_monitor()


def has_card():
    cardtype = AnyCardType()
    cardrequest = CardRequest( timeout=1, cardType=cardtype )

    try:
        cardservice = cardrequest.waitforcard()
    except:
        return False

    return True
