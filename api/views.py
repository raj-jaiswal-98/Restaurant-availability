from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
# from rest_framework.response import https
import uuid
from .models import Store_status, Store, Store_tz
from django.db.models import Q
from datetime import datetime, timedelta, time, date
from django.http import FileResponse
import pytz
from csv import DictWriter
# from rq import Queue
# from rq.job import Job
# from redis import Redis
# redis_conn = Redis()
# q = Queue(connection=redis_conn)  # no args implies the default queue

# tried implementing job queues using Redis, but could find a workaround for running Redis server on windows. :(

global job_queue   # glocal variable for storing which reports are ready and are currently being processed
job_queue = []


# the below code was for testing purpose

# now_utc = datetime.now(timezone('UTC'))
# print(now_utc.strftime(format))



# def as_timezone(datetime: time, tz):
#     return time.astimezone(timezone(tz))


# def tests():
#     timestamp = datetime.fromisoformat("2023-01-19T19:40:09.144581Z")
#     cnt = 0
#     # for _ in range(24):
#     #     tl = timestamp - timedelta(hours=1)    
#     #     # timezone = Store_tz.objects.filter(store_id=store_id)
        
#     #     for stores in Store_tz.objects.all():
#     #         store_id = stores.store_id
#     #         active = (1 if Store_status.objects.filter(Q(timestamp_utc__gte = tl) & Q(timestamp_utc__lte = timestamp) & Q(store_id = store_id) & Q(status = 1)).count() > 0 else 0)
#     #         cnt += active
#     #         print(f"{store_id} {active}")
#     #         if cnt > 10:
#     #             return "It workssss!!!!!!"
#     #     timestamp = timestamp - timedelta(hours=1)
        
#     # return "Nope!"
#     qr = Store.objects.filter(Q(store_id=904272797452687746) & Q(day_of_week = 0))
#     return qr.values()[0]['start_time_local']
#     # return datetime.fromisoformat(str(qr.values('timestamp_utc')[0]['timestamp_utc']))
# Create your views here.






def hourly_query(store_id, timestamp, local_timezone = "America/Chicago"): # 1 query
    uptime = 0
    downtime = 0
    # print(timestamp)
    tl = timestamp - timedelta(hours=1)
    x = Store_status.objects.filter( Q(timestamp_utc__lte = timestamp) & Q(timestamp_utc__gte = tl) & Q(store_id=store_id))
    if len(x) == 0:
        return uptime, downtime
    # print(x)
    if x.values('status')[0]['status'] == 1:
        uptime += 60
    else:
        downtime += 60
    
    return uptime, downtime


def daily_query(store_id, timestamp, local_timezone = "America/Chicago"):   # 4 queries
    uptime = 0
    downtime = 0
    # print(timestamp)
    tl = timestamp - timedelta(days=1)
    total_time_q = Store.objects.filter(Q(store_id=store_id) & Q(day_of_week = timestamp.isoweekday()-1))
    total_time = 24
    if len(total_time_q) != 0:
        open_time = total_time_q.values('start_time_local')[0]['start_time_local']
        end_time = total_time_q.values('end_time_local')[0]['end_time_local']
        diff = (datetime.combine(date.today(), end_time)-datetime.combine(date.today(), open_time))
        total_time = (diff.total_seconds()//60) / 60

    x = Store_status.objects.filter( Q(timestamp_utc__lte = timestamp) & Q(timestamp_utc__gte = tl) & Q(store_id=store_id) & Q(status=1)).count()
    
    uptime += x
    downtime += max(0, total_time - x)
    

    
    return uptime, downtime

def weekly_query(store_id, timestamp, local_timezone = "America/Chicago"): # 8 queries
    uptime = 0
    downtime = 0
    # print(timestamp)
    total_time = 0
    for i in range(7):                          # to find the total business hours of a shop
        total_time_q = Store.objects.filter(Q(store_id=store_id) & Q(day_of_week = i))
        ttl = 24
        if len(total_time_q) != 0:                           # handle case where data is incomplete
            open_time = total_time_q.values('start_time_local')[0]['start_time_local']
            end_time = total_time_q.values('end_time_local')[0]['end_time_local']
            diff = (datetime.combine(date.today(), end_time)-datetime.combine(date.today(), open_time))
            ttl = (diff.total_seconds()//60) // 60 # in hours
        total_time += ttl

    tl = timestamp - timedelta(days=7)
    
    x = Store_status.objects.filter( Q(timestamp_utc__lte = timestamp) & Q(timestamp_utc__gte = tl) & Q(store_id=store_id) & Q(status=1)).count()
    
    uptime += x
    downtime += max(0, total_time - x)
    
    return uptime, downtime

    










def generate_report():
    
    # job_queue.add(report_id)
    report_id = job_queue[-1]             # take the most recent request of report which needs to be generated
    
    curr_time = datetime.now(pytz.timezone('UTC'))
    curr_time -= timedelta(days=365)
    curr_time -= timedelta(days=15)
    field_names = ['store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week', 'downtime_last_hour', 'downtime_last_day', 'downtime_last_week']
    file_name = f"{report_id}.csv"
    stores = Store_tz.objects.all()
    
    with open(file_name, 'w') as csvfile:
        writer = DictWriter(csvfile, fieldnames = field_names)
        writer.writeheader()
        for store in stores:    # 13 queries for each store   complexity - > 13 * number_of_stores
            
            store_id = store.store_id
            timezone = store.timezone
            if len(timezone) == 0:   # default timezone is America/Chicago
                timezone = "America/Chicago"
            else:
                timezone = timezone
                                                                                    # perform 3 tasks
            uptime_hrs , dtime_hrs = hourly_query(store_id, curr_time, timezone)
            uptime_dy , dtime_dy = daily_query(store_id, curr_time, timezone)
            uptime_wk , dtime_wk = weekly_query(store_id, curr_time, timezone)
            
            writer.writerow({'store_id':store_id, 'uptime_last_hour': uptime_hrs, 'uptime_last_day': uptime_dy, 'uptime_last_week': uptime_wk, 'downtime_last_hour': dtime_hrs, 'downtime_last_day': dtime_dy, 'downtime_last_week': dtime_wk})
            
            
            

            
            
    print("Written successfully")
    job_queue.remove(report_id)
    # print(job_queue)
    return None


class ResponseThen(Response):                             # this is extended version of Response class, which runs a function after sending the request. Its a quick fix version of Job queues and workers.
    def __init__(self, data, then_callback, **kwargs):
        super().__init__(data, **kwargs)
        self.then_callback = then_callback

    def close(self):
        super().close()
        self.then_callback()


@api_view(['GET'])
def getData(request):  # this is just landing page type api function
    
    #now write query logic, everything is working fine...
    return Response("It works")
    
    

@api_view(['GET'])
def trigger_report(request):   # triggers report generation using current timestamp, returns report_id
    
    report_id = uuid.uuid4().int
    
    # job = Job.create(generate_report,id = report_id)
    # q.enqueue_job(job)
    # generate_report(report_id)
    
    job_queue.append(report_id)
    return ResponseThen(report_id, generate_report, status=status.HTTP_200_OK)

    # return Response(report_id)

@api_view(['GET'])
def get_report(request):
    # request.param
    report_id = request.GET['report_id']
    print(report_id)
    #now return the report

    # job = Job.fetch(id = report_id, connection=redis_conn)
    # if job.return_value() == None:
    #     return Response("Running!")
    if report_id in job_queue:
        return Response('Running!')
    
    file = open(f"{report_id}.csv", 'r')
    return Response(file)

