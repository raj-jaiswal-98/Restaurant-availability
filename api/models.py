from django.db import models
import pytz

TIMEZONES = tuple(zip(pytz.all_timezones, pytz.all_timezones))

# Create your models here.
class Store_tz(models.Model):
    store_id = models.BigIntegerField(primary_key = True, default = 1)
    timezone = models.CharField(max_length = 100, choices = TIMEZONES, default = 'America/Chicago') #defualt is UTC generally




class Store(models.Model):
    store_id = models.BigIntegerField()
    day_of_week = models.IntegerField()
    start_time_local = models.TimeField()
    end_time_local = models.TimeField()


class Store_status(models.Model):
    store_id = models.BigIntegerField()
    timestamp_utc = models.DateTimeField()
    status = models.IntegerField()


