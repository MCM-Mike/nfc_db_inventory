from time import sleep

from smartcard.CardConnectionObserver import ConsoleCardConnectionObserver
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString, toBytes

# define the apdus used in this script
GET_RESPONSE = [0XA0, 0XC0, 00, 00]
SELECT = [0xA0, 0xA4, 0x00, 0x00, 0x02]
DF_TELECOM = [0x7F, 0x10]


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
        (addedcards, removedcards) = actions
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

            #apdu = SELECT + DF_TELECOM
            #response, sw1, sw2 = card.connection.transmit(apdu)
            #if sw1 == 0x9F:
                #apdu = GET_RESPONSE + [sw2]
                #response, sw1, sw2 = card.connection.transmit(apdu)

        for card in removedcards:
            print("-Removed: ", toHexString(card.atr))

if __name__ == '__main__':
    print("Insert or remove a SIM card in the system.")
    print("This program will exit in 60 seconds")
    print("")
    cardmonitor = CardMonitor()
    selectobserver = selectDFTELECOMObserver()
    cardmonitor.addObserver(selectobserver)

    sleep(60)

    # don't forget to remove observer, or the
    # monitor will poll forever...
    cardmonitor.deleteObserver(selectobserver)

    import sys
    if 'win32' == sys.platform:
        print('press Enter to continue')
        sys.stdin.read(1)