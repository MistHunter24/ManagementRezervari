import mysql.connector

def DbReservationSave():
    mydb = mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "QAZxsw!234",
        database = "ReservationManagement"
    )
    
    return mydb
    
   
