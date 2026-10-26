{
    'name': 'Vehicle Rental Management',
    'version': '19.0.1.0',
    'category': 'Services/Fleet',
    'summary': 'Vehicle rental bookings, availability, charging, and invoice integration.',
    'description': '''
Vehicle Rental Management module for Odoo 19.

This addon provides a practical rental application layer on top of standard Odoo
Fleet, Contacts, and Accounting features. It allows users to manage vehicles,
bookings, pricing, customer reservations, and related accounting actions in a way
that remains consistent with native Odoo workflows.
''',
    'author': 'WS Solutions',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'fleet', 'contacts', 'account', 'calendar'],
    'data': [
        'security/ws_vehicle_rental_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/rental_booking_views.xml',
        'views/rental_menu.xml',
        'views/rental_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
