from flask import Blueprint, request, jsonify, send_file
import random , string
from psycopg2 import sql
from app.database import get_cursor_connection
import app.store as store
import multiprocessing
import psycopg2
from psycopg2 import sql
import config.config as config
from app.functions import reportGen, get_report_status




# Create a Blueprint for your routes
api = Blueprint('api', __name__)


# Define the /trigger_report endpoint
@api.route('/trigger_report', methods=['POST'])
def trigger_report():
    cursor,connection = get_cursor_connection()
    # Generate a random report_id 
    report_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    # Mark the report as not generated (FALSE) initially
    generated = False
    # Store the report in the database
    insert_query = "INSERT INTO reports (report_id, generated) VALUES (%s, %s);"
    cursor.execute(insert_query, (report_id, generated))
    connection.commit()
    
    p1 = multiprocessing.Process(target=reportGen, args=(report_id, )) 
    p1.start()

    # Return the report_id in the response
    response_data = {"report_id": report_id}
    return jsonify(response_data)


# Define the /get_report endpoint
@api.route('/get_report', methods=['GET'])
def get_report():
    report_id = request.args.get("report_id")
    if report_id is None:
        return "Missing Input"
    
    status = get_report_status(report_id)
    if status is None :
        return "An error occurred", 500
    
    if status != "Complete":
        return status
    
    try:
        csv_file_path = 'csvs/'+report_id+'.csv'
        return send_file(csv_file_path, as_attachment=True, download_name=report_id+'.csv')
    except FileNotFoundError :
        return "Missing CSV File, Please Generate Again, Process Might Have stopped", 500













