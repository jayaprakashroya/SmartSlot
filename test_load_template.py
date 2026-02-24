import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.template import engines

d = engines['django']
print('using dirs:', d.dirs)
try:
    t = d.get_template('vehicle_history.html')
    print('template loaded successfully')
    # render with empty context
    print('render result length', len(t.render({})))
except Exception as e:
    print('error loading/rendering', type(e), e)
