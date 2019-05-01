from datetime import datetime
import os
import sys

from sqlalchemy import create_engine, Column, ForeignKey, Date, String, engine, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

MYSQL_CONN_STR = 'mysql://root:root@localhost/nfc'


PRIVATE_KEY_LENGTH = 16


class NfcTag(db.Model):
    __tablename__ = 'nfc_tag'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    tag_id = db.Column(db.String(PRIVATE_KEY_LENGTH, 'ascii_bin'), nullable=False, primary_key=True)
    date_purchased = db.Column(Date)
    last_time_used = db.Column(Date)
    description = db.Column(Text(collation='utf8mb4_unicode_ci'), default='')
