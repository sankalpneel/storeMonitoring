import psycopg2
from psycopg2 import sql
import config.config as config
import app.database as db
import datetime
import app.functions as functions

class store:
    def __init__(self,store_id):
        self.store_id = store_id
        self.cursor,self.connection= db.get_cursor_connection()
        self.timezone = self.get_timeZone()
        self.business_hours = self.get_business_hours()
        

            
    #Fetching stores timezone from store_timezones table
    def get_timeZone(self):
        self.cursor.execute("SELECT timezone_str FROM store_timezones WHERE store_id = %s;", (self.store_id,))
        # Fetch the store's timezone
        timezone = self.cursor.fetchone()
        if timezone is not None:
            return timezone[0]
        else:
            return "America/Chicago"
        
    
    def get_business_hours(self):
        # Create a dictionary with default values for all days
        business_hours_dict = {i: (datetime.time(0, 0), datetime.time(0, 0)) for i in range(7)}
        
        # Execute a query to retrieve all business hours for the given store_id
        self.cursor.execute("SELECT day, start_time_local, end_time_local FROM store_business_hours WHERE store_id = %s;", (self.store_id,))

        # Fetch all business hours data
        business_hours = self.cursor.fetchall()

        if business_hours:
            # Create a dictionary to store business hours for each day
            business_hours_dict = {day: (start, end) for day, start, end in business_hours}
            
        return business_hours_dict
        
    
    # Suppose if start time is 9:00
    # We are finding the entry just before 9:00 to get its status 
    def get_inital_status(self,start_time):
        try:
            query = """
            SELECT status
            FROM store_activity
            WHERE store_id = %s
            AND timestamp_utc <= %s
            ORDER BY timestamp_utc DESC
            LIMIT 1;
            """
            self.cursor.execute(query, (self.store_id,start_time,))
            result = self.cursor.fetchone()
            if result:
                return result[0]  # Extract the 'status' value from the result
            else:
                return "active"  # Default value if no matching entry is found
        except Exception as e:
            return "active"  # Return "active" on error or no matching entry
        
        
    #get all store activity records in a time frame
    def get_activity_records(self,start_time, end_time):
        query = """
            SELECT status, timestamp_utc
            FROM store_activity
            WHERE store_id = %s
            AND timestamp_utc >= %s
            AND timestamp_utc <= %s
            ORDER BY timestamp_utc ASC;
            """ 
        self.cursor.execute(query,(self.store_id,start_time,end_time))
        entries = self.cursor.fetchall()
        return entries
    
    
    def last_hour(self,currTime):
        currTime = currTime.replace(minute=0, second=0, microsecond=0)
        day_number = currTime.weekday()
        
        busHour = self.business_hours.get(day_number)
        if busHour:
            closeTime = busHour[1]
            openTime = busHour[0]
        else:
            closeTime = datetime.time(23,59)
            openTime = datetime.time(0,0)
        
        inital = self.get_inital_status(currTime-datetime.timedelta(hours=1)) #if initally it was closed or not
        activity = self.get_activity_records(currTime-datetime.timedelta(hours=1),currTime)
        act =[]
        for x in range(len(activity)):
            act.append((functions.convert_to_timezone(activity[x][0],self.timezone),functions.convert_to_timezone(activity[x][1],self.timezone)))
        
        endTime = datetime.time(currTime.hour,currTime.minute)
        st = currTime - datetime.timedelta(hours=1)
        startTime = datetime.time(st.hour,st.minute)
        ct = startTime
        i =0 
        currUpTime=0
        if inital == "active":
            currUpTime=1
        up=0
        
        if len(activity)==0:
            if inital == "active":
                return 60,0
            else:
                return 0,60
        
        
        
        while ct < endTime and ct < datetime.time(11,59):
            if ct < openTime or ct > closeTime:
                up +=1
            elif i<len(activity):
                if datetime.time(activity[i][1].hour,activity[i][1].minute) == ct:
                    if activity[i][0] == "active":
                        currUpTime=1
                    else:
                        currUpTime=0
                    up += currUpTime
                    i += 1
            else:
                up += currUpTime
                
            hour = ct.hour
            minute = ct.minute
            minute +=1
            if minute == 60:
                minute=0
                hour+=1
            ct = datetime.time(hour,minute)
        
        
        return up, 60-up
    
    
    #Calculating last day by seprating it into hours   
    def last_day(self,currTime):
        # Calculate the previous day
        previous_day = currTime - datetime.timedelta(days=1)
        # Set the time to 12:00 AM
        iTime = previous_day.replace(hour=0, minute=0, second=0, microsecond=0)
        timeUpto = iTime+datetime.timedelta(days=1) 
        time_interval = datetime.timedelta(hours=1)
        iTime = iTime + time_interval
        minutes_up = 0.0
        minutes_down = 0.0
        while iTime < timeUpto:
            lh_up,lh_dt = self.last_hour(iTime)
            minutes_up += lh_up
            minutes_down += lh_dt
            iTime += time_interval
                
        return minutes_up/60,minutes_down/60
    
    
    def last_week(self,currTime):
        # Calculate the previous week's start date (previous Monday)
        previous_week_start = currTime - datetime.timedelta(days=(currTime.weekday() + 7))

        # Calculate the previous week's end date (previous Sunday)
        previous_week_end = previous_week_start + datetime.timedelta(days=6)
        current_date = previous_week_start
        one_day = datetime.timedelta(days=1)
        
        Tup,Tdw =0.0,0.0
        while current_date <= previous_week_end:
            wUp,wDw = self.last_day(current_date)
            Tup += wUp
            Tdw += wDw
            current_date += one_day
        return Tup,Tdw
                