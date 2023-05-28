import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="tp055241",
    password="tp055241",
)

my_cursor = mydb.cursor()

my_cursor.execute("CREATE DATABASE ldpms")

my_cursor.execute("SHOW DATABASES")

for db in my_cursor:
    print(db)