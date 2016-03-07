from functions import functions as f
### Startup
f.logsms(9,'Starting PySMS Server 1.0beta',0)
f.logsms(9,'Server is using the following parameters:',0)
f.logsms(9,'API: ' + f.api,0)
f.logsms(9,'URL: ' + f.url,0)
f.logsms(9,'Sendlog: ' + f.smslog,0)
f.logsms(9,'Errorlog: ' + f.errorlog,0)
f.logsms(9,'Proxy: ' + f.nvl(f.prox,'None'),0)
f.logsms(9,'PySMS Server 1.0beta started',0)
print('PySMS Server started')
### Startup
f.oracledb.open()

while 1:
	try:
		f.main()
		f.sleep(3)
	except (KeyboardInterrupt, SystemExit):
		f.logsms(9,'Stopping PySMS Server 1.0beta',0)
		print("Exiting...")
		f.logsms(9,'PySMS Server 1.0beta stopped',0)
		f.logsms(9,'############################',0)

		f.exit()
