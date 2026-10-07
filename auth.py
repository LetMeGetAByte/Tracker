import os
import jwt
import bcrypt
from typing import cast
from schema import OrgTable
from dotenv import load_dotenv
from sqlalchemy import select, insert, Connection, Row


class Auth:
    def __init__(self, sql_engine_con: Connection):
        self.econ = sql_engine_con

        load_dotenv()
        self.secret = os.getenv("SECRET")
        if self.secret is None:
            raise Exception("[Error] Secret is not set in env file.")
        self.secret = cast(str, self.secret)

    def find_org(self, name: str) -> Row[OrgTable] | None:
        try:
            return self.econ.execute(select(OrgTable).where(OrgTable.name == name)).one()
        except:
            return None

    def register(self, org: str, secret: str) -> tuple[bool, str]:
        if self.find_org(org):
            return (False, "Organization with matching name already exists.")

        secret_hash = bcrypt.hashpw(secret.encode(), bcrypt.gensalt())
        print(org, secret, secret_hash)
        self.econ.execute(insert(OrgTable).values(name=org, secret=secret_hash))
        self.econ.commit()

        return (True, "Registration successful.")

    def authenticate(self, org: str, secret: str) -> tuple[bool, str]:
        failure_msg = "Incorrect organization name or secret"
        print(org, secret)
        org_entry = self.find_org(org)
        if org_entry is None:
            return (False, failure_msg)

        secret_val = bcrypt.checkpw(secret.encode(), org_entry.secret)
        print(org, org_entry.secret, secret_val)
        if secret_val:
            payload = {"organization": org}
            token = jwt.encode(payload, self.secret)
            return (True, token)

        return (False, failure_msg)

    def validate(self, token: str) -> tuple[bool, str]:
        try:
            payload = jwt.decode(token, self.secret, algorithms="HS256")
            org = payload["organization"]
            return (True, org)
        except jwt.InvalidSignatureError:
            return (False, "Invalid token")
