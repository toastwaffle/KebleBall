# coding: utf-8
"""Logic regarding verification of affiliations."""

from __future__ import unicode_literals

import csv

import flask
import sqlalchemy

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

APP = app.APP
DB = db.DB


def verify_affiliation(user):
    """Mark the users affiliation as verified.

    For limited release, we require that the user's affiliation is verified.
    For current members with known battels accounts, this is done
    automatically, but for graduands, fellows, staff members etc an admin
    must manually check and approve them. This method is called when the
    affiliation is approved, and updates a flag before sending an email to
    the user reminding them to buy tickets.
    """
    user.affiliation_verified = True

    APP.email_manager.send_template(
        user.email,
        "Affiliation Verified - Buy Your Tickets Now!",
        "affiliation_verified.email",
        name=user.forenames,
        url=flask.url_for("purchase.purchase_home", _external=True),
    )

    DB.session.commit()


def use_list_affiliation(user):
    """Copy a user's affiliation from the affiliations list.

    The affiliation selected by the user when they register may not be the
    affiliation read from the affiliations list. This method forces the user's
    affiliation to the correct one.
    """
    if user.affiliation_list_entry is None:
        return False
    user.affiliation = user.affiliation_list_entry.affiliation
    verify_affiliation(user)
    return True


def deny_affiliation(user):
    """Mark the users affiliation as invalid.

    For limited release, we require that the user's affiliation is verified.
    For current members with known battels accounts, this is done
    automatically, but for graduands, fellows, staff members etc an admin
    must manually check and approve them. This method is called when the
    affiliation is rejected, and updates a flag accordingly.
    """
    user.affiliation_verified = False

    DB.session.commit()


def update_affiliation(user, new_college, new_affiliation):
    """Change the users affiliation.

    In order to maintain the verification of users' affiliations, when we
    update a college/affiliation we must re-submit it for verification as
    appropriate.
    """
    old_college = user.college
    old_affiliation = user.affiliation

    user.college = new_college
    user.affiliation = new_affiliation

    if (
        (old_affiliation != new_affiliation or old_college != new_college)
        and (
            new_college.name in APP.config["HOST_COLLEGES"]
            or new_affiliation.name == "Contest Winner"
        )
        and new_affiliation.name not in ["Other", "None"]
    ):
        user.affiliation_verified = None


def match_to_affiliation_list(user):
    from_email = models.AffiliationListEntry.get_by_email(user.email)
    if from_email is not None:
        if from_email.user is not None and from_email.user != user:
            flask.flash(
                (
                    "The email address provided is already associated with "
                    "another alumnus account. Please contact the ticketing "
                    "officer for assistance."
                ),
                "warning",
            )
            user.affiliation_list_entry = None
            user.affiliation_match = None
        else:
            user.affiliation_list_entry = from_email
            if (
                from_email.affiliation_reference
                and user.alumni_number
                and from_email.affiliation_reference == user.alumni_number
            ):
                user.affiliation_match = "Email & Alumni Number"
            else:
                user.affiliation_match = "Email only"
    elif user.alumni_number:
        from_alumni_number = models.AffiliationListEntry.get_by_affiliation_reference(
            user.alumni_number
        )
        if from_alumni_number is not None:
            if from_alumni_number.user is not None and from_alumni_number.user != user:
                flask.flash(
                    (
                        "The alumni number provided is already associated with "
                        "another alumnus account. Please contact the ticketing "
                        "officer for assistance."
                    ),
                    "warning",
                )
                user.affiliation_list_entry = None
                user.affiliation_match = None
            else:
                user.affiliation_list_entry = from_alumni_number
                user.affiliation_match = "Alumni Number only"
    else:
        user.affiliation_list_entry = None
        user.affiliation_match = None
    DB.session.commit()


def auto_verify(user):
    if user.affiliation_verified is None and (
        user.college.name not in APP.config["HOST_COLLEGES"]
        or user.affiliation.name in ["Other", "None"]
        or (user.battels is not None and user.affiliation.name == "Student")
        or (
            user.affiliation_list_entry is not None
            and user.affiliation_list_entry.affiliation == user.affiliation
        )
    ):
        user.affiliation_verified = True
        DB.session.commit()
        return True
    return False


def maybe_verify_affiliation(user):
    """Check if a user's affiliation can be verified

    Checks if a user's affiliation can be verified automatically, and
    otherwise sends an email to the ball ticketing officer to ask them to
    verify it manually
    """
    if user.affiliation_verified is None:
        match_to_affiliation_list(user)

        if auto_verify(user):
            return

        APP.email_manager.send_template(
            APP.config["TICKETS_EMAIL"],
            "Verify Affiliation",
            "verify_affiliation.email",
            user=user,
            url=flask.url_for("admin_users.verify_affiliations", _external=True),
        )
        flask.flash(
            (
                "Your affiliation must be verified before you will be "
                "able to purchase tickets. You will receive an email when "
                "your status has been verified. This process may take up to 24 "
                "hours."
            ),
            "warning",
        )


def get_unverified_users():
    """Get all the users who should be verified but aren't."""
    return (
        models.User.query.filter(
            (
                sqlalchemy.or_(
                    models.User.college.has(name=college)
                    for college in APP.config["HOST_COLLEGES"]
                )
            )
            | (models.User.affiliation_id == "8")
        )
        .filter(
            models.User.affiliation_verified
            == None  # pylint: disable=singleton-comparison
        )
        .all()
    )


def update_affiliation_list(new_list):
    """Update the affiliation list."""
    affiliations = {}
    for affiliation in models.Affiliation.query.all():
        affiliations[affiliation.name] = affiliation

    old_list_entries = {}
    for entry in models.AffiliationListEntry.query.all():
        old_list_entries[entry.email] = entry

    new_list_entries = {}
    for row in csv.DictReader(
        new_list.stream, fieldnames=["email", "affiliation", "affiliation_reference"]
    ):
        try:
            affiliation = affiliations[row["affiliation"]]
        except KeyError:
            flask.flash(
                "Unknown affiliation {affiliation} for {email}/{affiliation_reference}".format(
                    **row
                ),
                "error",
            )
            DB.session.rollback()
            return

        # Turn empty strings into None.
        email = row["email"] or None
        reference = row["affiliation_reference"] or None

        if email is None and reference is None:
            flask.flash(
                "List entries must have either an email or a reference", "error"
            )
            DB.session.rollback()
            return

        try:
            old_entry = old_list_entries[row["email"]]
            old_entry.affiliation = affiliation
            old_entry.affiliation_reference = reference
            new_list_entries[row["email"]] = old_entry
        except KeyError:
            entry = models.AffiliationListEntry(row["email"], affiliation, reference)
            DB.session.add(entry)
            new_list_entries[row["email"]] = entry

    for email, entry in old_list_entries.iteritems():
        if email not in new_list_entries:
            DB.session.delete(entry)

    DB.session.commit()

    flask.flash("Affiliation list updated", "success")
