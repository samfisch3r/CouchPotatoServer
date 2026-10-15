import unittest
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from couchpotato.core._base.scheduler import Scheduler


class SchedulerTest(unittest.TestCase):

    def setUp(self):
        self.scheduler = Scheduler.__new__(Scheduler)
        self.scheduler.crons = {}
        self.scheduler.intervals = {}
        self.scheduler.sched = BackgroundScheduler(
            job_defaults={'misfire_grace_time': 60}
        )
        self.scheduler.sched.start()
        self.scheduler.started = True

    def tearDown(self):
        self.scheduler.stop()

    def test_interval_jobs_are_scheduled_and_removed(self):
        self.scheduler.interval(
            identifier='test.interval',
            handle=lambda: None,
            minutes=5,
        )

        job = self.scheduler.intervals['test.interval']['job']
        self.assertEqual(job.trigger.interval, timedelta(minutes=5))
        self.assertEqual(job.misfire_grace_time, 60)

        self.scheduler.remove('test.interval')

        self.assertNotIn('test.interval', self.scheduler.intervals)
        self.assertIsNone(self.scheduler.sched.get_job(job.id))

    def test_cron_jobs_accept_wildcards(self):
        self.scheduler.cron(
            identifier='test.cron',
            handle=lambda: None,
            day='*',
            hour='*',
            minute='*/10',
        )

        job = self.scheduler.crons['test.cron']['job']
        fields = {field.name: str(field) for field in job.trigger.fields}
        self.assertEqual(fields['day'], '*')
        self.assertEqual(fields['hour'], '*')
        self.assertEqual(fields['minute'], '*/10')
