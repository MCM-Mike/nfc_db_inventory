import json
import base64
import warnings

from flask import Flask, Response, request, render_template
from flask_cors import CORS
from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.util import toHexString, toBytes
from smartcard.CardConnection import CardConnection

from models import NfcTag, MYSQL_CONN_STR, db

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_CONN_STR

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=sa_exc.SAWarning)
    db.init_app(app)


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


@app.route('/edit_nfctag', methods=['POST', 'GET'])
def edit_nfctag():

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

    message = ''

    if request.method == 'POST':
        #message = 'inside post'

        tag = NfcTag.query.get(uid)

        for column, value in request.form.items():
            setattr(tag, column, value)

        db.session.commit()

        message = "The tag data has been updated successfully"

    elif request.method == 'GET':

        #message = 'inside get'

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
        else:
            message = "Tag data has been read successfully"

    return render_template('nfctag_data.html', tag_id=tag.tag_id, description=tag.description, date_purchased=tag.date_purchased, last_time_used=tag.last_time_used, message=message)


if __name__ == '__main__':
    def set_wing_ide_debugger():
        import os
        if 'WINGDB_ACTIVE' in os.environ:
            app.debug = False

    set_wing_ide_debugger()
    app.run(port=5000)
