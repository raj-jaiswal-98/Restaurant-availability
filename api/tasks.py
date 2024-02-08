from workers import tasks

from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
import uuid
from .models import Store_status, Store, Store_tz
from django.db.models import Q
from datetime import datetime, timedelta, time, date
import pytz
from csv import DictWriter


def active_prev_hr(store_id, timestamp):
    tl = timestamp - timedelta(hours=1)    
    timezone = Store_tz.objects.filter(store_id=store_id)
    
    up, down = 0, 0
    
    if len(timezone) == 0:
        timezone = 'America/Chicago'
    else:
        timezone = timezone.values('timezone')[0]['timezone']
    
    # store is operating 24*7
    active = Store_status.objects.filter(Q(timestamp_utc__gte = tl) & Q(timestamp_utc__lte = timestamp) & Q(store_id = store_id) & Q(status = 1)).count()
        
    
    #convert local time to timestamp
    local_timestamp = timestamp.astimezone(pytz.timezone(timezone))
    day_of_week = timestamp.isoweekday()-1
    qr = Store.objects.filter(Q(store_id=store_id) & Q(day_of_week = day_of_week))
    open_local = time(0, 0, 0)
    close_local = time(23, 59, 59)
    if len(qr) != 0:
        x = qr.values('start_time_local', 'end_time_local')[0]
        open_local = x['start_time_local']
        close_local = x['end_time_local']
    
    local_time = local_timestamp.time()
    local_time1 = datetime.combine(date.today(), local_time) + timedelta(hours=1)
    local_time1 = local_time1.time()
    if (local_time >= open_local and local_time <= close_local) or (local_time1 <= open_local and local_time >= close_local):
        active = Store_status.objects.filter(Q(timestamp_utc__gte = tl) & Q(timestamp_utc__lte = timestamp) & Q(store_id = store_id)).order_by('-timestamp_utc')
        if len(active) > 0:
            
            diff = (datetime.combine(date.today(), local_time)-datetime.combine(date.today(), close_local))
            diff = diff.total_seconds()//60
            
            if active.values('status')[0]['status'] > 0:

                up += diff
                down += 60-diff # this can be improved by considering the proper length of business hours and making cases of segments of start_local and end_local
            else:
                down += 60-diff
                up += diff
    return up, down






@task()
def generate_report(report_id):
    
    curr_time = datetime.now(pytz.timezone('UTC'))

    field_names = ['store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week', 'downtime_last_hour', 'downtime_last_day', 'downtime_last_week']
    file_name = f"{report_id}.csv"
    stores = Store_tz.objects.all()
    tz_d = datetime.fromisoformat("2023-01-19T19:40:09.144581Z")
    curr_time = tz_d
    # print(curr_time)
    cur_time_week_before = curr_time - timedelta(days = 7)
    cur_time_day_before = curr_time - timedelta(hours = 24)
    cur_time_hour_before = curr_time - timedelta(hours = 1)
    with open(file_name, 'w') as csvfile:
        writer = DictWriter(csvfile, fieldnames = field_names)
        writer.writeheader()
        for store in stores:
            store_id = store.store_id
            timezone = store.timezone
            # data = {}
            # data['store_id']=store_id
            uptime_hrs , dtime_hrs = 0, 0
            uptime_dy , dtime_dy = 0, 0
            uptime_wk , dtime_wk = 0, 0
            for i in range(167):
                up, dw = active_prev_hr(store_id, curr_time)
                if i == 0:
                    uptime_hrs = up
                    dtime_hrs = dw
                if i < 6:
                    uptime_dy += up
                    dtime_dy += dw
                uptime_wk += up
                dtime_wk += dw
            
            # data['uptime_last_hour'] = uptime_hrs
            # data['uptime_last_week'] = uptime_wk
            # data['uptime_last_day'] = uptime_dy
            # data['downtime_last_hour'] = dtime_hrs
            # data['downtime_last_week'] = dtime_wk
            # data['downtime_last_day'] = dtime_dy
            writer.writerow({'store_id':store_id, 'uptime_last_hour': uptime_hrs, 'uptime_last_week': uptime_wk, 'downtime_last_hour': dtime_hrs, 'downtime_last_day': dtime_dy, 'downtime_last_week': dtime_wk})
    print("Written successfully")

    return None
        
