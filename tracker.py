import string
import sqlite3
import numpy as np
from typing import cast
from schema import URLTable, MetricTable
from urllib.parse import urlsplit, urlunsplit
from sqlalchemy import create_engine, select, insert, delete, asc, desc, func

DEFAULT_PATH = "store/tracker.db"

whitelist = list(string.ascii_letters + string.digits)


class Tracker:
    def __init__(self, path: str = DEFAULT_PATH):
        self.con = sqlite3.connect(path)
        self.engine = create_engine(f"sqlite:///{path}")

        self.cur = self.con.cursor()
        self.econ = self.engine.connect()

        self.__init_tables()

    def __init_tables(self):
        # enable foreign keys
        self.cur.execute("PRAGMA foreign_keys = ON")
        # organization table
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS organization("
            "id INTEGER PRIMARY KEY,"
            "name TEXT UNIQUE NOT NULL,"
            "secret TEXT NOT NULL,"
            "reg_time TEXT DEFAULT CURRENT_TIME"
            ")"
        )
        # url table
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS url("
            "id INTEGER PRIMARY KEY,"
            "org_id INTEGER REFERENCES organization(id),"
            "tag TEXT NOT NULL UNIQUE,"
            "scheme TEXT,"
            "netloc TEXT,"
            "path TEXT,"
            "query TEXT,"
            "fragment TEXT"
            ")"
        )
        # metrics table
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS metric("
            "id INTEGER PRIMARY KEY,"
            "tag TEXT REFERENCES url(tag),"
            "ip TEXT NOT NULL,"
            "timestamp TEXT DEFAULT CURRENT_TIMESTAMP"
            ")"
        )

        self.con.commit()

    def __generate_tag(self, n=6):
        tag = "".join(np.random.choice(whitelist, size=n))
        query = select(URLTable).where(URLTable.tag == tag)
        while len(self.econ.execute(query).fetchall()) > 1:
            tag = "".join(np.random.choice(whitelist, size=n))
        return tag

    def __record(self, tag: str, ip: str):
        self.econ.execute(insert(MetricTable).values(tag=tag, ip=ip))
        self.econ.commit()

    def track(self, url: str, org_id: int) -> str:
        tag = self.__generate_tag()
        url_parts = urlsplit(url)
        self.econ.execute(
            insert(URLTable).values(
                org_id=org_id,
                tag=tag,
                scheme=url_parts[0],
                netloc=url_parts[1],
                path=url_parts[2],
                query=url_parts[3],
                fragment=url_parts[4],
            )
        )
        self.econ.commit()

        return tag

    def delete(self, tag: str):
        self.econ.execute(delete(MetricTable).where(MetricTable.tag == tag))
        self.econ.execute(delete(URLTable).where(URLTable.tag == tag))
        self.econ.commit()

    def get_url(self, tag: str, ip: str) -> str:
        query = self.econ.execute(select(URLTable).where(URLTable.tag == tag))
        url = urlunsplit(query.fetchall()[0][3:])
        self.__record(tag, ip)
        return cast(str, url)

    def get_stats(self, tag: str, org_id: int) -> dict:
        # TODO: implement org_id validation for tag
        total_clicks_query = self.econ.execute(
            select(func.count()).select_from(MetricTable).where(MetricTable.tag == tag)
        )
        total_clicks = total_clicks_query.scalar() or 0

        clicks_by_ip_query = self.econ.execute(
            select(MetricTable.ip, func.count())
            .select_from(MetricTable)
            .group_by(MetricTable.ip)
            .where(MetricTable.tag == tag)
        )
        clicks_by_ip = [
            {"ip": row[0], "count": row[1]} for row in clicks_by_ip_query.all()
        ]

        return {"total_clicks": total_clicks, "clicks_by_ip": clicks_by_ip}
