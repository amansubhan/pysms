import urllib.request as req
from urllib.request import Request
from urllib.error import URLError, HTTPError
from socket import timeout
import xml.etree.ElementTree as ET
import datetime, time, glob, os, urllib.parse, configparser, sys
from functions import oracledb

global api, smslog, errorlog, url, values, failedcount, rc, rs

srvlog = 'log/srv.log'
failedcount = 0

config = configparser.ConfigParser(allow_no_value=True)
config.read('config')

api = config["API"]["api"].replace("'",'')
url = config["API"]["url"].replace("'",'')
smslog = config["LOG"]["smslog"].replace("'",'')
errorlog = config["LOG"]["errorlog"].replace("'",'')
table = config["ORACLE"]["smstable"].replace("'",'')
logt = config["ORACLE"]["logtable"].replace("'",'')
failedt = config["ORACLE"]["failedtable"].replace("'",'')

if config["API"]["proxy"].replace("'",'') != '':
	proxy = req.ProxyHandler({'http': config["API"]["proxy"].replace("'",'')})
	opener = req.build_opener(proxy, req.HTTPHandler)
	prox = config["API"]["proxy"].replace("'",'')
else:
	opener = req.build_opener(req.HTTPHandler)
	prox = None


req.install_opener(opener)

def dt():
	dt = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
	return dt

def sleep(s):
	time.sleep(s)
	return 

def getfailedcount():
	global	failedcount
	return failedcount

def setfailedcount(num):
	global failedcount
	if num == 0:
		failedcount = 0
	else:
		failedcount += 1

def suspend():
	with open('/tmp/suspend','w') as a:
		a.write('Y')
		a.close()

def resume():
	with open('/tmp/suspend','w') as a:
		a.write('N')
		a.close()

def suspended():
	with open('/tmp/suspend','r') as s:
		status = s.read()
		s.close()
	return status

def apihealth():
	try:
		re = req.urlopen(url,timeout=2)
	except (HTTPError, URLError) as error:
		status = error
	except timeout:
		status = 'timeout'
	except Exception as h:
		status = h
	else:
		status = re.code
	if status == 200:
		apistatus = 'Up'
	else:
		apistatus = 'Down'
		suspend()
	with open('/tmp/apistatus','w') as a:
		a.write(apistatus)
		a.close()
	return apistatus

def logsms(level,log,num):
	if level == 0:   ## on success
		with open(smslog, 'a') as f:
			f.write(api + ': ' + dt() + ' : ' + str(num) + ' : ' + log + '\n')
			f.close()
		oracledb.insert('INSERT INTO '+ logt +' (API, DATETIME, CELLNO, LOG) VALUES (:a, SYSDATE, :n , :l)',{'a':api, 'n':num, 'l':log})
		oracledb.commit()
	elif level == 1: ## on failure
		with open(errorlog,'a') as f:
			f.write(api + ': ' + dt() + ' : ' + str(num) + ' : ' + log + '\n')
			f.close()
		oracledb.insert('INSERT INTO '+ failedt +' (API, DATETIME, CELLNO, LOG) VALUES (:a, SYSDATE, :n , :l)',{'a':api, 'n':num, 'l':log})
		oracledb.commit()
	elif level == 2: ## write to failed log
		oracledb.insert('INSERT INTO '+ failedt +' (API, DATETIME, CELLNO, LOG) VALUES (:a, SYSDATE, :n , :l)',{'a':api, 'n':num, 'l':log})
		oracledb.commit()
	elif level == 9: ## server logs
		with open(srvlog,'a') as f:
			f.write(dt() +' : '+ log + '\n')
			f.close()
	else:	## unknown errors
		with open(errorlog, 'a') as f:
			f.write("Unkown Error: " + api + ': ' + dt() + ' : ' + log + '\n')
			f.close()
		oracledb.insert('INSERT INTO '+ failedt +' (API, DATETIME, CELLNO, LOG) VALUES (:a, SYSDATE, :n , :l)',{'a':api, 'n':num, 'l':log})
		oracledb.commit()

def sendsms(num, msg):
	values = {'action' : 'sendmessage', 'username' : 'younustml', 'password' : 'Y0u2uStxtl', 'recipient' : num, 'messagedata' : msg, 'originator' : '8874' }
	data = urllib.parse.urlencode(values)
	data = data.encode('utf-8') # data should be bytes

	try:
	    resp = req.urlopen(url, data, timeout=1)
	except (HTTPError, URLError) as e:
		logsms(1,str('Failed to reach api, reason: ' + str(e)),num)
		sent = 'failed'
	except timeout:
		status = 'timeout'
		logsms(1,str('Failed to reach api, reason: ' + str(status)),num)
		sent = 'failed'
	except Exception as e:
		status = e
		logsms(1,str('Failed to reach api, reason: ' + str(status)),num)
		sent = 'failed'
	else:
		data = ET.fromstring(resp.read())
		action = data[0].text
		if action == 'error':
			logsms(1,data[1][1].text,num)
			sent = 'failed'
		else:
			if "ERROR" in data[1][0][1].text:
				logsms(1,data[1][0][1].text,num)
				sent = 'failed'
			else:
				logsms(0,data[1][0][1].text,num)
				sent = 'success'
		return sent

def checkapi():
	count = 0
	sleeptime = 5
	while apihealth() != 'Up' or getfailedcount() >= 3:
		count += 1
		if count > 3:
			sleeptime = sleeptime + 5
			count = 0
		sleep(sleeptime)
		if sendsms('0332','Test Message') == 'success':
					setfailedcount(0)
	else:
		resume()
		logsms(1,'Server is back, resuming...',0)

def fetchallsms():
	global rc, rs
	sql = "SELECT ID,NUM,MSG FROM " + table
	rs = oracledb.select(sql)
	rc = rs[0]
	rs = rs[1] 	
	return rc,rs

def delsms(a):
	oracledb.delete('DELETE FROM SMS WHERE ID = :i',{'i':a})
	oracledb.commit()

def nvl(var, val):
  if (var is None or var == ''):
    return val
  return var

def processSMS():
	global rc, rs
	fetchallsms()
	if rc != 0:
		for i in range(rc):
			id = rs[i][0]
			num = rs[i][1]
			a = rs[i][2]
			msg = a.replace('%0A','\n')
			i += 1

			if suspended() == 'N':
				if sendsms(num,msg) != 'success':
					setfailedcount(1)
					if getfailedcount() >= 3:
						logsms(1,'Too many tries, suspending...',0)
						suspend()
				else:
					delsms(id)
			else:
				checkapi()

def main():
	resume()
	apihealth()
	if apihealth() == "Up" and suspended() == 'N':
		processSMS()

def exit():
	oracledb.close()
	sys.exit(1)
