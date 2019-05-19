# coding: utf-8
"""Database model for ticket addons."""

from __future__ import unicode_literals
from __future__ import division

from eisitirio import app
from eisitirio.database import db

DB = db.DB
APP = app.APP


class TicketAddon(DB.Model):
    """Model for entries on affiliation lists."""

    __tablename__ = "ticket_addon"

    slug = DB.Column(DB.Unicode(120), nullable=False)
    price = DB.Column(DB.Integer(), nullable=False)
    cancelled = DB.Column(DB.Boolean(), default=False, nullable=False)

    ticket_id = DB.Column(DB.Integer, DB.ForeignKey("ticket.object_id"), nullable=False)
    ticket = DB.relationship("Ticket", backref=DB.backref("addons", lazy="dynamic"))

    def __init__(self, slug, price, ticket):
        self.slug = slug
        self.price = price
        self.ticket = ticket

    def __repr__(self):
        return "<TicketAddon {0}: {1} for ticket #{2}>".format(
            self.object_id, self.addon_type, self.ticket_id
        )
