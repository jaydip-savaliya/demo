# -*- coding: utf-8 -*-
###############################################################################
#
# Aspire Softserv Pvt. Ltd.
# Copyright (C) Aspire Softserv Pvt. Ltd.(<https://aspiresoftserv.com>).
#
###############################################################################
{
    "name": "Automatic Multi Company Selection",
    "category": "Base",
    "summary": "Keep allowed companies selected by defult when user logs in.",
    "version": "18.0.0.1.0",
    "price": 9.99,
    "license": "AGPL-3",
    'description': """
        In Odoo, user may be granted with access to multiple companies. This module helps you keep all allowed companies enabled when user logs in. However, user can belong to only a single compnay. The module also select the native company upon login.
    """,
    "author": "Aspire Softserv Pvt. Ltd",
    "website": "https://aspiresoftserv.com",
    "depends": ['web'],
    'assets': {
        'web.assets_backend': [
            'aspl_select_multi_company/static/src/js/company_service.js',
        ],
    },
    "application": True,
    "installable": True,
    "maintainer": "Aspire Softserv Pvt. Ltd",
    "support": "odoo@aspiresoftserv.com",
}
