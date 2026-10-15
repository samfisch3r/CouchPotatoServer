from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from couchpotato.core.event import addEvent
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin

log = CPLog(__name__)

autoload = 'Scheduler'


class Scheduler(Plugin):

    crons = {}
    intervals = {}
    started = False

    def __init__(self):

        self.crons = {}
        self.intervals = {}
        addEvent('schedule.cron', self.cron)
        addEvent('schedule.interval', self.interval)
        addEvent('schedule.remove', self.remove)
        addEvent('schedule.queue', self.queue)

        self.sched = BackgroundScheduler(job_defaults = {'misfire_grace_time': 60})
        self.sched.start()
        self.started = True

    def remove(self, identifier):
        for cron_type in ['intervals', 'crons']:
            jobs = getattr(self, cron_type)
            scheduled = jobs.pop(identifier, None)
            if scheduled:
                try:
                    self.sched.remove_job(scheduled['job'].id)
                except JobLookupError:
                    log.debug('%s job %s was already removed', (cron_type.capitalize(), identifier))
                else:
                    log.debug('%s unscheduled %s', (cron_type.capitalize(), identifier))

    def doShutdown(self, *args, **kwargs):
        self.stop()
        return super(Scheduler, self).doShutdown(*args, **kwargs)

    def stop(self):
        if self.started:
            log.debug('Stopping scheduler')
            self.sched.shutdown(wait = False)
            log.debug('Scheduler stopped')
        self.started = False

    def cron(self, identifier = '', handle = None, day = '*', hour = '*', minute = '*'):
        log.info('Scheduling "%s", cron: day = %s, hour = %s, minute = %s', (identifier, day, hour, minute))

        self.remove(identifier)
        self.crons[identifier] = {
            'handle': handle,
            'day': day,
            'hour': hour,
            'minute': minute,
            'job': self.sched.add_job(handle, 'cron', day = day, hour = hour, minute = minute)
        }

    def interval(self, identifier = '', handle = None, hours = 0, minutes = 0, seconds = 0):
        log.info('Scheduling %s, interval: hours = %s, minutes = %s, seconds = %s', (identifier, hours, minutes, seconds))

        self.remove(identifier)
        self.intervals[identifier] = {
            'handle': handle,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'job': self.sched.add_job(handle, 'interval', hours = hours, minutes = minutes, seconds = seconds)
        }

        return True

    def queue(self, handlers = None):
        if not handlers: handlers = []

        for h in handlers:
            h()

            if self.shuttingDown():
                break

        return True
