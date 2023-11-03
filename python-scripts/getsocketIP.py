import socket
port=9999
for i in range(2,140):
	remoteIP='192.168.0.'+'{0:03d}'.format(i)
	sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	result = sock.connect_ex((remoteIP, port))
	if result == 0:
		print(remoteIP)
		sock.close()
		exit()
	sock.close()
exit(2)

