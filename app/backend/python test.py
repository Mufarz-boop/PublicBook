import mysql.connector

db = mysql.connector.connect(
    host="10.96.239.103",
    user="publicbook",
    password="layanan publik",
    database="db_publicbook"
)

print("berhasil connect")