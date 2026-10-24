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

def get_all_routes(routes, prefix=""):
    collected = []
    for r in routes:
        if hasattr(r, 'methods') and hasattr(r, 'path'):
            collected.append((r.methods, prefix + r.path))
        elif hasattr(r, 'routes'):
            collected.extend(get_all_routes(r.routes, prefix))
        elif hasattr(r, 'original_router') and hasattr(r.original_router, 'routes'):
            sub_prefix = prefix + (getattr(getattr(r, 'include_context', None), 'prefix', '') or '')
            collected.extend(get_all_routes(r.original_router.routes, sub_prefix))
    return collected

all_routes = get_all_routes(app.routes)
route_paths = set()
for methods_set, path in all_routes:
    methods = ', '.join(sorted(methods_set))
    print(f'  [{methods}] {path}')
    route_paths.add(path)

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
for methods_set, path in all_routes:
    for nr in new_routes:
        if path == nr and nr not in checked:
            methods = ', '.join(sorted(methods_set))
            print(f'  [{methods}] {path}')
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