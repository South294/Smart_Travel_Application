from main import app

print('=== App Info ===')
print(f'Title: {app.title}')
print(f'Version: {app.version}')
print()

print('=== All Routes ===')
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        methods = ', '.join(sorted(route.methods))
        print(f'  [{methods}] {route.path}')

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
import inspect
# Check if on_event is used
src = inspect.getsource(app)
if 'on_event' in src:
    print('WARNING: Still using on_event deprecated handler')
else:
    print('OK: No on_event deprecated handler found')

if 'lifespan' in src:
    print('OK: Using lifespan event handler')
else:
    print('WARNING: No lifespan handler found')