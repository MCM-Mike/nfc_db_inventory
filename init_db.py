from sqlalchemy import engine, create_engine

from models import NfcTag, MYSQL_CONN_STR, db

def _parse_connection_string(mysql_conn_str):
    db_url = engine.url.make_url(mysql_conn_str)
    db_address = '{}://{}:{}@{}'.format(db_url.drivername, db_url.username, db_url.password, db_url.host)
    return db_url.database, db_address


db_name, db_address = _parse_connection_string(MYSQL_CONN_STR)

myengine = create_engine(MYSQL_CONN_STR)
db.Model.metadata.drop_all(myengine)
db.Model.metadata.create_all(myengine)
