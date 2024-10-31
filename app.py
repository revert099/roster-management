"""
Roster Management System developed for ICT299
Author: Jacob Winsor

Dependencies required:
    Flask:      A python web framework (pip install flask)
    csv:        Used for accessing and writing to a CSV file
    datetime:   Used to generate time and date for clock-in/out requests
    uuid:       Used to create a unique-id for each clock-in entry

Description:
    This is a Flask based web application that allows helpdesk students to clock-in and clock-out of their shifts.
    It reads student details (Name and Student number) from a csv file and displays them in a drop-down menu.
    A student finds their details through the drop-down menu and either clocks in or out.
    There is error checking to determine whether a user is already clocked in or out.

    There are three main routes used in the program:
        1. '/'          - The homepage where students find their details
        2. '/clock_in'  - Handles clock-in functionality. Writes a clock-in entry, unique-id and time-date on request
        3. '/clock_out' - Handles clock-out functionality. Updates the CSV file to include clock-out time and status on request

Storing CSV files:
    The students.csv file is to be placed in the parent directory of the application.
    It must include the header "name,number" and have the data formatted as such.

    The clock_in_data.csv file will be output to the parent directory of the application.
    It can also be pre-made and placed into the file.
"""

from flask import Flask, render_template, request, redirect, session, flash
import csv                          # for csv manipulation
from datetime import datetime       # for generating date & time
import uuid                         # to create a unique identifier
import os

app = Flask(__name__)
# Needed to use session, secret key stored in render environment
app.secret_key = 'MY_SECRET_KEY' #os.getenv('VERY_SECRET_KEY')  
if not app.secret_key:
    raise ValueError("No secret key set for Flask application")

# function to load student data from an students.csv
def load_students():
    # initialise empty students list to store data loaded from students.csv
    students = []
    # open students.csv file in read mode
    with open('students.csv', mode='r', newline='') as file:
        reader = csv.reader(file)                                   # create a csv reader object
        next(reader)                                                # skip the header
        for row in reader:                                          # iterate over CSV until EOF
            students.append({'name': row[0], 'number': row[1]})     # Append each student name and number to the students list
            # print(f'Name: {row[0]}, Number: {row[1]}')            # for debugging
    # return students array from input CSV
    return students

# app.route to load student data and render the homepage
@app.route('/')
def index():
    # Get students data from CSV file to display on homepage
    student_data = load_students()    
    # Get sessions of clocked in students, or create an empty dictionary                              
    clocked_in_students = session.get('clocked_in_students', {})    
    # Check clock in status to flash a message via HTML
    for student in student_data:
        student_number = student['number']
        # Set clocked_in status based on current session state
        student['clocked_in'] = student_number in clocked_in_students and clocked_in_students[student_number]['clocked_in']
    return render_template('index.html', students=student_data,
                           clocked_in_students=clocked_in_students) # render index.html

# app.route to handle clock-in functionality
@app.route('/clock_in', methods=['POST'])
def clock_in():
    students = load_students()
    # Retrieve clocked-in students from flask session, or create an empty one if one is not present
    clocked_in_students = session.get('clocked_in_students', {})
    # Get student number from the submitted form to determine student clocking in
    student_number = request.form['student_number']
    # find the student name based on student number
    for student in students:
        if student['number'] == student_number:
            student_name = student['name']
            break

    # check if student is already clocked in. If they are -  flash a message to screen to let the user know
    if student_number in clocked_in_students and clocked_in_students[student_number]['clocked_in']:
        flash("Error: you are already clocked in")
        # redirect to index
        return redirect('/')
    
    # generate a unique-id and clock-in time
    unique_id = str(uuid.uuid4())[:8]
    clock_in_time = datetime.now().strftime('%H:%M:%S %d-%m-%Y')

    # Save clock-in record in a CSV file
    with open('clock_in_data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([student_number, student_name, unique_id, clock_in_time, "", "clock-in"])

    # Update session to track clocked-in students
    clocked_in_students[student_number] = {
        'name': student_name,
        'clock_in_time': clock_in_time,
        'unique_id': unique_id,
        'clocked_in': True  # Set clocked-in status to True
    }
    session['clocked_in_students'] = clocked_in_students

    return redirect('/')

# app.route to handle clock_out functionality
@app.route("/clock_out", methods=['POST'])
def clock_out():

    clocked_in_students = session.get('clocked_in_students', {})
    student_number = request.form['student_number']

    # If student is not clocked-in - flash a message to screen to inform them
    if student_number not in clocked_in_students or not clocked_in_students[student_number]['clocked_in']:
        flash("Error: you are not clocked in")
        # redirect to index
        return redirect('/')
    
    # capture time and date for clock_out event
    clock_out_time = datetime.now().strftime('%H:%M:%S %d-%m-%Y')

    # Update clock-in record in the CSV file with clock-out time
    # initialise empty list to store clock_in data to be updated
    rows = []                             
    updated = False                                     
    with open('clock_in_data.csv', mode='r') as file:
        reader = csv.reader(file)
        # fill/update rows
        for row in reader:                  # look for clocked-in student
            if len(row) >= 6 and row[0] == student_number and row[2] == clocked_in_students[student_number]['unique_id'] and row[5] == "clock-in":
                row[4] = clock_out_time     # update row 4 to time student pressed clock out
                row[5] = "clock-out"        # append row 5 from 'clock-in' to 'clock-out'
                updated = True              # mark student as updated
            rows.append(row)
    # Write updated row to CSV file
    with open('clock_in_data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)
    # Update session to mark student as clocked out
    clocked_in_students[student_number]['clocked_in'] = False
    session['clocked_in_students'] = clocked_in_students
    # redirect to index
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Get the PORT from environment or default to 5000
    app.run(debug=True, host='0.0.0.0', port=port)

