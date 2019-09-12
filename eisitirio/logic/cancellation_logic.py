# coding: utf-8
"""Logic for cancelling tickets."""

from __future__ import unicode_literals

import collections

import flask_login as login

# from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

APP = app.APP
DB = db.DB


def cancel_tickets(tickets, quiet=False):
    """Cancel a set of tickets.

    Constructs a series of refund transactions. There is a separate refund
    transaction for each transaction used for payment.
    """
    if quiet:

        def flash(_, unused):
            """No-op flash function for admin cancellations."""
            pass

    else:
        flash = flask.flash

    transactions = collections.defaultdict(list)

    cancelled = []

    if login.current_user.held_ticket and login.current_user.held_ticket in tickets:
        remaining_claimed_tickets = []
        remaining_unclaimed_tickets = []
        for ticket in login.current_user.active_tickets.all():
            if ticket in tickets:
                continue
            if ticket.holder is not None:
                remaining_claimed_tickets.append(ticket)
            else:
                remaining_unclaimed_tickets.append(ticket)
        if remaining_claimed_tickets and not remaining_unclaimed_tickets:
            flask.flash(
                (
                    "You cannot cancel your own ticket without also cancelling "
                    'your guest tickets. Contact <a href="{0}">the ticketing '
                    "officer</a> for assistance."
                ).format(APP.config["TICKETS_EMAIL_LINK"]),
                "error",
            )
            return []

    for ticket in tickets:
        if not ticket.can_be_cancelled():
            continue
        if not ticket.paid or ticket.payment_method == "Free":
            if ticket.holder == login.current_user and remaining_unclaimed_tickets:
                remaining_unclaimed_tickets[0].holder = login.current_user
                remaining_unclaimed_tickets[0].claims_made += 1
            ticket.cancelled = True
            ticket.holder = None
            for addon in ticket.addons.all():
                addon.cancelled = True
            cancelled.append(ticket)
        # no longer allow refunds for card transactions
        elif ticket.payment_method in ["Battels"]:
            transactions[ticket.transaction].append(ticket)

    DB.session.commit()

    for transaction, tickets in transactions.iteritems():
        refund_transaction = models.BattelsTransaction(transaction.user)

        DB.session.add(refund_transaction)

        for ticket in tickets:
            DB.session.add(
                models.TicketTransactionItem(refund_transaction, ticket, is_refund=True)
            )

        number_uncancelled = sum(
            1 for ticket in transaction.tickets if not ticket.cancelled
        )

        # Refund the postage if we're cancelling all the tickets in the
        # transaction (which haven't already been cancelled)
        if len(tickets) == number_uncancelled and transaction.postage:
            DB.session.add(
                models.PostageTransactionItem(
                    refund_transaction, transaction.postage, is_refund=True
                )
            )

        DB.session.commit()

        success = False

        if transaction.battels_term == "MTHT" and app.APP.config["CURRENT_TERM"]:
            refund_transaction.charge("MTHT")
            success = True
        else:
            refund_transaction.charge(app.APP.config["CURRENT_TERM"])
            success = True

        if success:
            cancelled.extend(tickets)

            for ticket in tickets:
                if ticket.holder == login.current_user and remaining_unclaimed_tickets:
                    remaining_unclaimed_tickets[0].holder = login.current_user
                    remaining_unclaimed_tickets[0].claims_made += 1
                ticket.cancelled = True
                ticket.holder = None

            if refund_transaction.postage:
                refund_transaction.postage.cancelled = True

            DB.session.commit()

    if cancelled:
        APP.log_manager.log_event(
            "Cancelled tickets", tickets=cancelled, user=login.current_user
        )

        if len(cancelled) == len(tickets):
            flash("All of the tickets you selected have been cancelled.", "success")
        else:
            flash(
                (
                    "Some of your tickets could not be automatically "
                    "refunded, and so were not cancelled. This might be due to "
                    "them having been payed for by card. If they have not been purchased by card you can try again "
                    "later, but if this problem continues to occur, you "
                    'should contact <a href="{0}">the ticketing officer</a>'
                ).format(APP.config["TICKETS_EMAIL_LINK"]),
                "warning",
            )
    else:
        flash(
            (
                "None of your tickets could be automatically refunded, and so "
                "none were cancelled.  This might be due to "
                "them having been paid for by card. If they have not been purchased by card you can try again "
                "later, but if this problem continues to occur, you "
                'should contact <a href="{0}">the ticketing officer</a>'
            ).format(APP.config["TICKETS_EMAIL_LINK"]),
            "warning",
        )

    return cancelled
