from datetime import datetime

#from flask_sqlalchemy import SQLAlchemy

import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

MYSQL_CONN_STR = 'mysql://root:root@localhost/nfc'

Base = declarative_base()


PRIVATE_KEY_LENGTH = 16


class NfcTag(Base):
    __tablename__ = 'nfc_tag'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    tag_id = Column(String(PRIVATE_KEY_LENGTH, 'ascii_bin'), nullable=False, primary_key=True)





if __name__ == '__main__':
    #def create_tables(MYSQL_CONN_STR):

        #db_name, db_address = _parse_connection_string(mysql_conn_str)

        #engine = sqlalchemy.create_engine(db_address)
        #engine.execute('CREATE DATABASE IF NOT EXISTS {}'.format(db_name))
        #engine = sqlalchemy.create_engine(mysql_conn_str)
        #db.Model.metadata.create_all(engine) # maybe in separate routine?


    def _parse_connection_string(mysql_conn_str):
        db_url = engine.url.make_url(mysql_conn_str)
        db_address = '{}://{}:{}@{}'.format(db_url.drivername, db_url.username, db_url.password, db_url.host)
        return db_url.database, db_address


    db_name, db_address = _parse_connection_string(MYSQL_CONN_STR)

    myengine = create_engine(MYSQL_CONN_STR)

    # create nfc db manually for now
    #myengine.execute('CREATE DATABASE {}'.format(db_name))

    #myengine.execute('CREATE DATABASE IF NOT EXISTS {}'.format(db_name))

    Base.metadata.create_all(myengine)

