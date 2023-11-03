import datetime
import pytz
import os
from app.database import get_cursor_connection, close_database_connection
import app.store as st


def get_report_status(report_id):
    try:
        cursor,connection = get_cursor_connection()
        if cursor is None:
            return None
        # Execute a query to retrieve the generated status for the provided report_id
        cursor.execute("SELECT generated FROM reports WHERE report_id = %s;", (report_id,))
        
        # Fetch the report data
        report_data = cursor.fetchone()
        
        close_database_connection(cursor,connection)
        if report_data is not None:
            generated = report_data[0]
        
            if generated:
                return "Complete"
            else:
                return "Running"
        else:
            return "no such report found"

    except Exception as e:
        # Handle any database or connection errors here
        return f"Error: {str(e)}"
    

def get_unique_store_ids(cursor):
    try:
        cursor.execute("SELECT DISTINCT store_id FROM store_activity;")
        # Fetch all unique store_ids
        unique_store_ids = [record[0] for record in cursor.fetchall()]
        return unique_store_ids

    except Exception as e:
        # Handle any database or connection errors here
        return f"Error: {str(e)}"
    



# utc to store time
def convert_to_timezone(utc_datetime, timezone_str):
    try:
        utc_datetime = pytz.UTC.localize(utc_datetime)  # Make sure the input datetime is in UTC
        target_timezone = pytz.timezone(timezone_str)
        converted_datetime = utc_datetime.astimezone(target_timezone)
        return converted_datetime
    except Exception as e:
        return f"Error: {e}"
    



 # Function to generate and save a CSV file
def generate_csv_file(name, report_data):
    directory = 'csvs'  # Specify the directory where you want to save the CSV file
    os.makedirs(directory, exist_ok=True)  # Create the directory if it doesn't exist

    file_content = "store_id,uptime_last_hour,uptime_last_day,uptime_last_week,downtime_last_hour,downtime_last_day,downtime_last_week\n"

    # Assuming that all arrays in report_data have the same length
    num_items = len(report_data["store_id"])
    
    for i in range(num_items):
        store_id = report_data["store_id"][i]
        lh_up = report_data["uptime_last_hour"][i]
        hUp = report_data["uptime_last_day"][i]
        Tup = report_data["uptime_last_week"][i]
        lh_dt = report_data["downtime_last_hour"][i]
        hDw = report_data["downtime_last_day"][i]
        Tdw = report_data["downtime_last_week"][i]
        
        row = f"{store_id},{lh_up},{hUp},{Tup},{lh_dt},{hDw},{Tdw}\n"
        file_content += row

    with open("csvs/"+name+".csv", "w", newline='') as file:
        file.write(file_content)
        

    
def reportGen(report_id):
    cursor,connection = get_cursor_connection()
    current = '2023-01-25 18:13:22.47922'
    currTime = datetime.datetime.strptime(current, '%Y-%m-%d %H:%M:%S.%f')        
    report_data = {
            "store_id": [],
            "uptime_last_hour": [],"uptime_last_day": [],"uptime_last_week": [],
            "downtime_last_hour": [],"downtime_last_day": [],"downtime_last_week": [],
        }
    try:
        unique_store_ids = get_unique_store_ids(cursor)        
        i=0
        for store_id in unique_store_ids :
            Store = st.store(store_id) 
            weekUp,weekDw = Store.last_week(currTime)
            hourUp,hourDown = Store.last_hour(currTime)
            dayUp,dayDown = Store.last_day(currTime)
            
            report_data["store_id"].append(store_id)
            report_data["uptime_last_hour"].append(hourUp)
            report_data["uptime_last_day"].append(dayUp)
            report_data["uptime_last_week"].append(weekUp)
            report_data["downtime_last_hour"].append(hourDown)
            report_data["downtime_last_day"].append(dayDown)
            report_data["downtime_last_week"].append(weekDw)
            print_progress_bar(i, len(unique_store_ids))
            i+=1
    finally:
        # SQL query to update the 'generated' column to True
        sql_query = f"UPDATE reports SET generated = True WHERE report_id = '{report_id}'"
        # Execute the SQL query
        cursor.execute(sql_query)
        # Commit the changes to the database
        connection.commit()
        cursor.close()
        
    
    generate_csv_file(report_id,report_data)
    
    
    
def print_progress_bar(current, total, length=50):
    progress = current / total
    arrow = '=' * int(length * progress)
    spaces = ' ' * (length - len(arrow))
    percentage = progress * 100

    print(f'[{arrow}{spaces}] {percentage:.2f}%', end='\r')
    
    

