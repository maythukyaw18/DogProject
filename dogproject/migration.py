import sqlite3  
  
con = sqlite3.connect("dog.db")  
print("Database opened successfully")  
  
con.execute("create table Dogs (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")  
  
print("Table created successfully")  
  
con.close()  