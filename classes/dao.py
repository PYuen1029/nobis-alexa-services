import json
import pprint


class DAO:
    def __init__(self, db):
        self.db = db

    def query(self, query):
        rows = self.db.query(query).as_dict()
        self.db.transaction().commit()
        return rows

    def query_first(self, query):
        rows = self.db.query(query).first()
        self.db.transaction().commit()
        return rows

    def get_config(self):
        rows = self.query_first('select * from config')
        return json.loads(rows.get('data'))
