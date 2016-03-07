import cx_Oracle
import configparser
import sys

global db, status, host, port, sid, dbuser, dbpassword, database

config = configparser.ConfigParser(allow_no_value=False)
config.read('config')

host = config["ORACLE"]["host"].replace("'",'')
port = config["ORACLE"]["port"].replace("'",'')
sid = config["ORACLE"]["sid"].replace("'",'')
dbuser = config["ORACLE"]["dbuser"].replace("'",'')
dbpassword = config["ORACLE"]["dbpassword"].replace("'",'')
database = host+':'+port+'/'+sid

srvlog = 'log/srv.log'

def open():
	global db, status, dbuser, dbpassword, database
	try: 
		db = cx_Oracle.connect(dbuser, dbpassword, database)
	except Exception as e:
		status = 'failed'
		print('Database connection failure. Reason: ' + str(e))
		with open(srvlog,'a') as f:
			f.write('Oracle Error: ' + str(e) + '\n')
			f.close()
		sys.exit(1)
	else:
		status = 'success'
		#print('Database connection succeeded')
	return status,db

def select(sql):
	global db,status
	rc = 0
	rs = 0
	c = db.cursor()
	try:
		c.execute(sql)
	except Exception as e:
		print('SQL Execution error: ' + str(e))
		with open(srvlog,'a') as f:
			f.write('Oracle Error: ' + str(e) + '\n')
			f.close()
	else:
		rs = c.fetchall()
		rc = c.rowcount
	return rc,rs

def insert(sql,var):
	global db,status
	c = db.cursor()
	try:
		c.execute(sql,var)
	except Exception as e:
		print('SQL Execution error: ' + str(e))
		with open(srvlog,'a') as f:
			f.write('Oracle Error: ' + str(e) + '\n')
			f.close()

def delete(sql,var):
	global db,status
	c = db.cursor()
	try:
		c.execute(sql,var)
	except Exception as e:
		print('SQL Execution error: ' + str(e))
		with open(srvlog,'a') as f:
			f.write('Oracle Error: ' + str(e) + '\n')
			f.close()

def commit():
	global db
	try:
		db.commit()
	except Exception as e:
		with open(srvlog,'a') as f:
			f.write('Oracle Error: ' + str(e) + '\n')
			f.close()


def close():
	global db, status
	if status == 'failed':
		print('Connection not open')
	else:
		try:
			db.close()
		except Exception as e:
			with open(srvlog,'a') as f:
				f.write('Oracle Error: ' + str(e) + '\n')
				f.close()
		#print('Database connection closed')
