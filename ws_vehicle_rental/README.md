# Vehicle Rental Management

This module is designed for Odoo 19 and adds a rental booking layer for standard Odoo Fleet vehicles.

## Included functionality
- Booking creation and status lifecycle
- Vehicle availability checks for overlapping dates
- Default rental pricing configuration
- Customer and invoice linkage
- Fleet vehicle rental eligibility flag
- Odoo menu and configuration views

## Notes
This repository has not been executed inside a live Odoo 19 database in this environment, so installation and runtime validation remain unverified here.

## Installation
1. Copy the `ws_vehicle_rental` folder into your Odoo `addons` directory.
2. Update the app list.
3. Install the module.
4. Configure the `Vehicle Rental` menu and default pricing values from the Settings area.

## Design choices
This solution keeps the module focused on Odoo-native Fleet, Contacts, and Accounting integration and avoids modifying Odoo core source files.
