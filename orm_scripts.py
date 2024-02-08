from api.models import Store_tz, Store, Store_status
from datetime import time
from datetime import datetime as dt
from django.db import connection
from csv import DictReader


def run():
    #timezones
    Store_tz.objects.all().delete()
    with open('store timezones.csv', 'r') as csvfile:
        reader = DictReader(csvfile)
        for row in reader:
            Store_tz.objects.create(store_id = int(row['store_id']), timezone = row['timezone_str'])


    #open hours
    Store.objects.all().delete()
    with open('Menu hours.csv', 'r') as csvfile:
        reader = DictReader(csvfile)
        for row in reader:
            Store.objects.create(store_id = int(row['store_id']), day_of_week = int(row['day']), start_time_local = time.fromisoformat(row['start_time_local']), end_time_local = time.fromisoformat(row['end_time_local']))
    
    
    print("Menu hours  done!!")
    #status
    # Store_status.objects.all().delete()
    with open('store status.csv', 'r') as csvfile:
        reader = DictReader(csvfile)
        for row in reader:
            Store_status.objects.create(store_id = int(row['store_id']), timestamp_utc = dt.fromisoformat(f"{row['timestamp_utc'][0:-4]}+00:00"), status = (True if row['status'] == 'active' else False))
    
    
    print('done!!')

run()
