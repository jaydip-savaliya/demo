# -*- coding: utf-8 -*-
###############################################################################
#
# Aspire Softserv Pvt. Ltd.
# Copyright (C) Aspire Softserv Pvt. Ltd.(<https://aspiresoftserv.com>).
#
###############################################################################
{
    "name": "Project Invoice",
    "category": "Accounting",
    "summary": "Project Timesheet Invoice",
    "version": "18.0.0.1.0",
    "price": 50.00,
    "license": "AGPL-3",
    "author": "Aspire Softserv Pvt. Ltd",
    "website": "https://aspiresoftserv.com",
    'description': """
        This module automates the process of generating detailed invoices based on project timesheet data, ensuring accurate and efficient billing procedures.
    """,
    "depends": ['hr', 'account', 'hr_timesheet', 'l10n_in'],
    "data": [
        "security/ir.model.access.csv",
        'views/account_analytic_line.xml',
        'views/project_configuration.xml',
        'views/res_partner_inherit.xml',
        'views/payment_swift_details_view.xml',
        'views/invoice_view_inherit.xml',
        'views/res_partner_bank_details.xml',
        'report/invoice_report.xml',
        'wizards/project_invoice_popup.xml',
        'wizards/product_change_timesheet.xml',
    ],
    "application": True,
    "installable": True,
    "maintainer": "Aspire Softserv Pvt. Ltd",
    "support": "odoo@aspiresoftserv.com",
    "images": ['static/description/banner.gif'],
}
