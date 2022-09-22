from unittest import result
from flask import Flask, render_template, request
from datetime import datetime
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__, template_folder='html')

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


# Home Page
@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html', date=datetime.now())


# About Us
@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com', date=datetime.now())


# Add Employee
@app.route("/addemp", methods=['POST'])
def addEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']
    check_in = ''

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location, check_in))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name, date=datetime.now())

# Add Employee Done
@app.route("/addemp/",methods=['GET','POST'])
def addEmpDone():
    return render_template('index.html', date=datetime.now())


# Employee Attendance Check In
@app.route("/attendance/checkIn",methods=['GET','POST'])
def checkIn():
    emp_id = request.form['emp_id']

    update_stmt = "UPDATE employee SET check_in =(%(check_in)s) WHERE emp_id = %(emp_id)s"
    cursor = db_conn.cursor()

    LoginTime = datetime.now()
    formatted_login = LoginTime.strftime('%Y-%m-%d %H:%M:%S')
    print ("Check in time:{}",formatted_login)
        
    try:
        cursor.execute(update_stmt, { 'check_in': formatted_login ,'emp_id':int(emp_id)})
        db_conn.commit()
        print(" Data Updated into MySQL")

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

    return render_template('attendanceOutput.html', emp_id, loginTime=formatted_login, date=datetime.now())

# Employee Attendance Checkout
@app.route("/attendance/checkOut",methods=['GET','POST'])
def checkOut():

    emp_id = request.form['emp_id']
    select_stmt = "SELECT check_in FROM employee WHERE emp_id = %(emp_id)s"
    insert_sql = "INSERT INTO attendance (emp_id, loginTime, checkout, totalWorkingHours) VALUES (%s,%s,%s,%s)"

    cursor = db_conn.cursor()
        
    try:
        cursor.execute(select_stmt,{'emp_id':int(emp_id)})
        LoginTime= cursor.fetchall()
       
        for row in LoginTime:
            formatted_login = row
            print(formatted_login[0])
        
        CheckoutTime = datetime.now()
        LogininDate = datetime.strptime(formatted_login[0],'%Y-%m-%d %H:%M:%S')
      
        formatted_checkout = CheckoutTime.strftime('%Y-%m-%d %H:%M:%S')
        Total_Working_Hours = CheckoutTime - LogininDate
        print(Total_Working_Hours)
         
        try:
            cursor.execute(insert_sql, (emp_id, formatted_login[0], formatted_checkout, Total_Working_Hours))
            db_conn.commit()            
            
        except Exception as e:
             return str(e)
                    
    except Exception as e:
        return str(e)

    finally:
        cursor.close()
        
    return render_template("AttendanceOutput.html", Checkout = formatted_checkout, 
     LoginTime=formatted_login[0], TotalWorkingHours=Total_Working_Hours, date=datetime.now())

# Get Employee Done
@app.route("/attendance/",methods=['GET','POST'])
def atdEmpDone():
    
    return render_template('index.html', date=datetime.now())


# Get Employee Information
@app.route("/fetchdata",methods=['GET','POST'])
def getEmp():
     emp_id = request.form['emp_id']

     select_stmt = "SELECT * FROM employee WHERE emp_id = %(emp_id)s"
     cursor = db_conn.cursor()
        
     try:
         cursor.execute(select_stmt, { 'emp_id': int(emp_id) })
         for result in cursor:
            print(result)
        

     except Exception as e:
        return str(e)
        
     finally:
        cursor.close()

     return render_template('GetEmpOutput.html', result=result, date=datetime.now())

# Get Employee Done
@app.route("/fetchdata/",methods=['GET','POST'])
def getEmpDone():
    
    return render_template('index.html', date=datetime.now())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
