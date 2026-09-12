import inspect
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent / 'src' / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

import main
from main import app

print('=== App Info ===')
print(f'Title: {app.title}')
print(f'Version: {app.version}')
print()

print('=== All Routes ===')
route_paths = set()
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        methods = ', '.join(sorted(route.methods))
        print(f'  [{methods}] {route.path}')
        route_paths.add(route.path)

required_routes = {
    '/api/auth/login',
    '/api/tours',
    '/api/bookings',
    '/api/ai/chat',
    '/api/payments/vnpay/create',
    '/api/guides/me/dashboard',
    '/api/admin/dashboard'
}
missing_routes = required_routes - route_paths
assert not missing_routes, f'Missing required routes: {sorted(missing_routes)}'

print()
print('=== Key New Routes ===')
new_routes = ['/api/guides/assign', '/api/guides/unassigned-tours', '/api/guides/{id}/assign-tour', '/api/admin/guides/assign']
checked = set()
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        for nr in new_routes:
            if route.path == nr and nr not in checked:
                methods = ', '.join(sorted(route.methods))
                print(f'  [{methods}] {route.path}')
                checked.add(nr)

print()
print('=== Deprecation Check ===')
# Check if on_event is used
src = inspect.getsource(main)
if 'on_event' in src:
    print('WARNING: Still using on_event deprecated handler')
else:
    print('OK: No on_event deprecated handler found')

if 'lifespan' in src:
    print('OK: Using lifespan event handler')
else:
    print('WARNING: No lifespan handler found')

print('OK: Required route assertions passed')