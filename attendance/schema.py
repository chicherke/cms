import graphene
from graphql_jwt.decorators import permission_required, login_required
from graphene_django.types import DjangoObjectType
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from graphene_django.filter import DjangoFilterConnectionField
from datetime import date, datetime, timedelta
from django.conf import settings
from members.models import Group
import json
from .generatorScript import generatorScript

from django.utils import timezone

from .api.log import Query as logQuery

to_tz = timezone.get_default_timezone()


class AttendanceLogObj(graphene.ObjectType):
    id = graphene.String()


def update_futureSSID(futureSSID):
    seed = 1000
    if len(futureSSID) > 2:
        seed = futureSSID[-1]
    while len(futureSSID) < 10000:
        futureSSID.append(generatorScript(seed))
        seed = futureSSID[-1]
    with open("attendance/futureSSID.json", "w") as file:
        json.dump(futureSSID, file)

class LogAttendance(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        list = graphene.List(graphene.String)

    Output = AttendanceLogObj

    def mutate(self, info, username, password, list):
        with open("attendance/futureSSID.json", "r") as file:
            futureSSID = json.load(file)
            if len(futureSSID) == 0:
                # current SSID must always be at index 2, adding 2 dummy values to get it to
                # index 2
                futureSSID.append('DummyValue1')
                futureSSID.append('DummyValue2')
                update_futureSSID(futureSSID)

        time = datetime.now() - timedelta(minutes=5)
        recentLogsCount = Log.objects.filter(lastSeen__gte=time).count()

        user = User.objects.get(username=username)
        if user:
            if check_password(password, user.password):

                now = datetime.now().astimezone(to_tz)

                groups = Group.objects.filter(members__in=[user], attendanceEnabled=True)

                # check if member is part of any group, that has attendance enabled
                if groups.count() > 0:
                    for group in groups:
                        module = group.attendanceModule

                        # get details from thread
                        ssid = module.SSID

                        refreshInterval = module.seedRefreshInterval

                        # convert refresh interval to minutes
                        refreshMins = refreshInterval.seconds / 60
                        giveAttendance = False
                        if recentLogsCount == 0:
                            currentSSID = -1
                            for sentSSID in list:
                                try:
                                    if int(sentSSID.strip('amFOSS_')) in futureSSID:
                                        currentSSID = int(sentSSID.strip('amFOSS_'))
                                except ValueError:
                                    pass
                            if currentSSID != -1:
                                
                                # The NodeMCU might stop at two windows, at the 5 minute mark 
                                # or in between the 5 minute interval.
                                # For the first case time-5 is being used and stored at 
                                # index 1 while latter time-10 is 
                                # stored at index 0. The currentSSID is at Index 2.
                                # DummyValues used ot keep currentSSID at 
                                # position 2 after recognising it

                                giveAttendance = True
                                futureSSID = ['DummyValue1', 'DummyValue2'] + futureSSID[futureSSID.index(currentSSID):]
                                module.SSID = 'amFOSS_' + str(futureSSID[2])
                                module.seed = futureSSID[2]
                                module.lastRefreshTime = now.replace(second=0, microsecond=0)
                                module.save()
                                with open("attendance/futureSSID.json", "w") as file:
                                    json.dump(futureSSID, file)
                            else:
                                raise Exception('Node and Server are out of sync')
                        else:
                            if module.SSID in list:
                                giveAttendance = True
                        # check for matching ssid from list
                        if giveAttendance:

                            # Compute start time & end time for the current session

                            # Start Time =  Current Time - Current Minute % refreshInterval (in mins)
                            startTime = now - timedelta(
                                                    minutes=now.minute%refreshMins,
                                                    seconds=now.second,
                                                    microseconds=now.microsecond
                                                )

                            # End Time = Current Time + refreshInterval
                            endTime = startTime + refreshInterval

                            # create session object
                            session = {"start": startTime.isoformat(), "end": endTime.isoformat()}

                            # Checks if logs exist already for today
                            logs = Log.objects.filter(member=user, date=now.date())

                            # if logs exist for today, update existing log adding the current session
                            if logs.count() != 0:
                                log = logs[0]

                                prevSessions = log.sessions
                                prev = json.loads(prevSessions)

                                log.lastSeen = now

                                # check if session is not already marked
                                if prev[-1] != session:
                                    prev.append(session)
                                    log.sessions = json.dumps(prev)
                                    log.duration += refreshInterval

                                    # Add thread if not in days thread
                                    if module not in log.modules.all():
                                        log.modules.add(module)

                                log.save()

                                return AttendanceLogObj(id=log.id)

                            # else create a new log for the day
                            else:
                                log = Log.objects.create(
                                    member=user,
                                    date=now.date(),
                                    sessions=json.dumps([session]),
                                    duration=refreshInterval,
                                    lastSeen=now
                                )
                                log.modules.add(module)
                                log.save()
                                return AttendanceLogObj(id=log.id)
                        else:
                            raise Exception('Matching SSID Not Found')
                raise Exception('User not member of any group, or attendance for the group is not enabled')
            raise Exception('Wrong Password')
        raise Exception('User does not exist')

class Mutation(object):
    LogAttendance = LogAttendance.Field()

class attendanceModuleObj(graphene.ObjectType):
    SSID = graphene.String()
    lastRefreshTime = graphene.types.datetime.DateTime()
    lastRefresh = graphene.String()

    def resolve_lastRefreshTime(self, info):
        return self['lastRefreshTime'].astimezone(to_tz)

    def resolve_lastRefresh(self, info):
        time = self['lastRefreshTime'].astimezone(to_tz)
        return time.strftime("%H:%M:%S:%f")

class Query(logQuery):
    attendanceModule = graphene.Field(attendanceModuleObj, id=graphene.Int(required=True))

    @login_required
    def resolve_attendanceModule(self, info, **kwargs):
        id = kwargs.get('id')
        return Module.objects.values().get(id=id)
