# coding: utf-8

from kebleball.app import app
from kebleball.database.ticket import Ticket
from kebleball.database.user import User
from kebleball.database.waiting import Waiting

def canBuy(user):
    if not app.config['TICKETS_ON_SALE']:
        if app.config['LIMITED_RELEASE']:
            if not (
                    user.college.name == "Keble" and
                    user.affiliation.name in [
                        "Student",
                        "Graduand",
                        "Staff/Fellow",
                        "Foreign Exchange Student",
                    ]
            ):
                return (
                    False,
                    0,
                    (
                        u"tickets are on limited release to current Keble members and "
                        u"Keble graduands only."
                    )
                )
            elif not user.affiliation_verified:
                return (
                    False,
                    0,
                    (
                        u"your affiliation has not been verified yet. You will be "
                        u"informed by email when you are able to purchase tickets."
                    )
                )
        else:
            return (
                False,
                0,
                (
                    u'tickets are currently not on sale. Tickets may become available '
                    u'for purchase or through the waiting list, please check back at a '
                    u'later date.'
                )
            )

    # Don't allow people to buy tickets unless waiting list is empty
    if Waiting.query.count() > 0:
        return (
            False,
            0,
            u'there are currently people waiting for tickets.'
        )

    unpaidTickets = user.tickets \
        .filter(Ticket.cancelled==False) \
        .filter(Ticket.paid==False) \
        .count()

    if unpaidTickets >= app.config['MAX_UNPAID_TICKETS']:
        return (
            False,
            0,
            (
                u'you have too many unpaid tickets. Please pay '
                u'for your tickets before reserving any more.'
            )
        )

    ticketsOwned = user.tickets \
        .filter(Ticket.cancelled==False) \
        .count()

    if app.config['TICKETS_ON_SALE']:
        if ticketsOwned >= app.config['MAX_TICKETS']:
            return (
                False,
                0,
                (
                    u'you already own too many tickets. Please contact <a href="{0}">the '
                    u'ticketing officer</a> if you wish to purchase more than {1} '
                    u'tickets.'
                ).format(
                    app.config['TICKETS_EMAIL_LINK'],
                    app.config['MAX_TICKETS']
                )
            )
    elif app.config['LIMITED_RELEASE']:
        if ticketsOwned >= app.config['LIMITED_RELEASE_MAX_TICKETS']:
            return (
                False,
                0,
                (
                    u'you already own {0} tickets. During pre-release, only {0} '
                    u'tickets may be bought per person.'
                ).format(
                    app.config['LIMITED_RELEASE_MAX_TICKETS']
                )
            )

    ticketsAvailable = app.config['TICKETS_AVAILABLE'] - Ticket.count()

    if ticketsAvailable <= 0:
        return (
            False,
            0,
            (
                u'there are no tickets currently available. Tickets may become '
                u'available for purchase or through the waiting list, please '
                u'check back at a later date.'
            )
        )

    if app.config['TICKETS_ON_SALE']:
        max_tickets = app.config['MAX_TICKETS']
    elif app.config['LIMITED_RELEASE']:
        max_tickets = app.config['LIMITED_RELEASE_MAX_TICKETS']

    return (
        True,
        min(
            ticketsAvailable,
            app.config['MAX_TICKETS_PER_TRANSACTION'],
            max_tickets - ticketsOwned,
            app.config['MAX_UNPAID_TICKETS'] - unpaidTickets
        ),
        None
    )

def canWait(user):
    waitingOpen = app.config['WAITING_OPEN']

    if not waitingOpen:
        return (
            False,
            0,
            u'the waiting list is currently closed.'
        )

    ticketsOwned = user.tickets \
        .filter(Ticket.cancelled==False) \
        .count()
    if ticketsOwned >= app.config['MAX_TICKETS']:
        return (
            False,
            0,
            (
                u'you have too many tickets. Please contact <a href="{0}">the '
                u'ticketing officer</a> if you wish to purchase more than {1} '
                u'tickets.'
            ).format(
                app.config['TICKETS_EMAIL_LINK'],
                app.config['MAX_TICKETS']
            )
        )

    waitingFor = user.waitingFor()
    if waitingFor >= app.config['MAX_TICKETS_WAITING']:
        return (
            False,
            0,
            (
                u'you are already waiting for too many tickets. Please rejoin '
                u'the waiting list once you have been allocated the tickets '
                u'you are currently waiting for.'
            )
        )

    return (
        True,
        min(
            app.config['MAX_TICKETS_WAITING'] - waitingFor,
            app.config['MAX_TICKETS'] - ticketsOwned
        ),
        None
    )
