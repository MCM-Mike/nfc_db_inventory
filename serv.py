import json
import base64

from flask import Flask, Response
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.util import toHexString, toBytes
from smartcard.CardConnection import CardConnection

from models import NfcTag, MYSQL_CONN_STR, Base

app = Flask(__name__)
CORS(app)


engine = create_engine(MYSQL_CONN_STR)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


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

    new_tag = NfcTag(tag_id=uid)
    session.add(new_tag)
    session.commit()


    return Response(json.dumps(uid), mimetype='application/json')


if __name__ == '__main__':
    def set_wing_ide_debugger():
        import os
        if 'WINGDB_ACTIVE' in os.environ:
            app.debug = False

    set_wing_ide_debugger()
    app.run(port=5000)
