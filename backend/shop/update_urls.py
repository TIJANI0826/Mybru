#!/usr/bin/env python
"""Update urls.py to add cart endpoints"""

import sys
import os

# Change to the shop directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open('urls.py', 'r') as f:
    lines = f.readlines()

# Find the line with oauth_views import and add cart_views
output = []
for i, line in enumerate(lines):
    output.append(line)
    if 'from . import oauth_views' in line and 'cart_views' not in ''.join(lines):
        output.append('from . import cart_views\n')

# Now find where to add cart endpoints
final_output = []
for i, line in enumerate(output):
    final_output.append(line)
    if "name='google_oauth_login')," in line and 'cart/add' not in ''.join(output):
        # Add cart endpoints after google_oauth_login
        final_output.append('    # Cart endpoints\n')
        final_output.append("    path('cart/', cart_views.get_user_cart, name='get_user_cart'),\n")
        final_output.append("    path('cart/add/', cart_views.add_to_cart, name='add_to_cart'),\n")
        final_output.append("    path('cart/update/', cart_views.update_cart_item, name='update_cart_item'),\n")
        final_output.append("    path('cart/remove/', cart_views.remove_from_cart, name='remove_from_cart'),\n")
        final_output.append("    path('cart/clear/', cart_views.clear_cart, name='clear_cart'),\n")

with open('urls.py', 'w') as f:
    f.writelines(final_output)

print('Updated urls.py with cart_views import and endpoints')
