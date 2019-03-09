#Auth WP Asura dev team
#RESTserver for fetching data from Thai national id card
#19/11/2018

from flask import Flask, Response
from flask_cors import CORS
from smartcard.CardConnection import CardConnection
from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.util import toHexString, toBytes
import json
import base64

app = Flask(__name__)
CORS(app)


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


@app.route('/get_data')
def get_data():
    cardtype = AnyCardType()
    cardrequest = CardRequest( timeout=1, cardType=cardtype )

    try:
        cardservice = cardrequest.waitforcard()
    except:
        resultdict = {
            'status':'inactive'
        }
        return json.dumps(resultdict)

    stat = cardservice.connection.connect()

    command = toBytes('FF CA 00 00 00')
    response, sw1, sw2 = cardservice.connection.transmit(command)
    uid = toHexString(response).replace(' ','')
    return Response(json.dumps(uid), mimetype='application/json')


if __name__ == '__main__':
    def set_wing_ide_debugger():
        import os
        if 'WINGDB_ACTIVE' in os.environ:
            app.debug = False

    set_wing_ide_debugger()
    app.run(port=5000)
