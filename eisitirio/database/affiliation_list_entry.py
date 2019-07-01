# coding: utf-8
"""Database model for entries on the affiliation list."""

from __future__ import unicode_literals
from __future__ import division

from eisitirio import app
from eisitirio.database import db

DB = db.DB
APP = app.APP


class AffiliationListEntry(DB.Model):
    """Model for entries on the affiliation list."""

    __tablename__ = "affiliation_list_entry"

    email = DB.Column(DB.Unicode(120), unique=True, nullable=True)
    affiliation_reference = DB.Column(DB.Unicode(30), unique=True, nullable=True)

    affiliation_id = DB.Column(
        DB.Integer, DB.ForeignKey("affiliation.object_id"), nullable=False
    )
    affiliation = DB.relationship(
        "Affiliation", backref=DB.backref("affiliation_list_entries", lazy="dynamic")
    )

    def __init__(self, email, affiliation, affiliation_reference=None):
        self.email = email
        self.affiliation = affiliation
        self.affiliation_reference = affiliation_reference

    def __repr__(self):
        return "<AffiliationListEntry {0}: {1} is {2}>".format(
            self.object_id, self.email, self.affiliation.name
        )
