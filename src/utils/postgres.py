import logging
import os
import psycopg2


class Postgres():
    def __init__(self):
        self._logger = logging.getLogger()
        self._con = None

    def __enter__(self):
        self._begin()
        return self

    def __exit__(self, *exc):
        e_type, e_val, _ = exc
        try:
            if e_type:
                self._logger.error("Exception object: %s" % e_type)
                self._logger.error("Exception detail: %s" % e_val)
                self._rollback()
            else:
                self._commit()
        finally:
            self._end()

    def _begin(self):
        self._con = psycopg2.connect(os.environ.get("DATABASE_URL")) 

    def _commit(self):
        if self._con:
            self._con.commit()
        else:
            raise Exception("No database connection. Commit failed")

    def _rollback(self):
        if self._con:
            self._con.rollback()
        else:
            raise Exception("No database connection. Rollback failed")

    def _end(self):
        if self._con:
            self._con.close()
            self._logger.info("Connection closed.")

    def execute(self, sql, params=None):

        with self._con.cursor() as cursor:
            if params:
                ret = cursor.execute(sql, params)
            else:
                ret = cursor.execute(sql)
        return ret

    def select(self, sql, params=None):
        cursor = self._con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor
