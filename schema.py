from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel

class CredRequest(BaseModel):
    organization: str
    secret: str

class Base(DeclarativeBase):
    pass

class URLTable(Base):
    __tablename__ = "url"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organization.id"))
    tag: Mapped[str] = mapped_column(nullable=False, unique=True)
    scheme: Mapped[str] = mapped_column()
    netloc: Mapped[str] = mapped_column()
    path: Mapped[str] = mapped_column()
    query: Mapped[str] = mapped_column()
    fragment: Mapped[str] = mapped_column()

class MetricTable(Base):
    __tablename__ = "metric"

    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(ForeignKey("url.tag"))
    ip: Mapped[str] = mapped_column()
    timestamp: Mapped[str] = mapped_column()

class OrgTable(Base):
    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    secret: Mapped[str] = mapped_column(nullable=False, unique=True)
    reg_time: Mapped[str] = mapped_column()
