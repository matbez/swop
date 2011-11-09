'''
Program Klient
do wymiany danych medycznych z uzyciem standardu HL7
w ramach projektu SWOP
oraz pracy inzynierskiej
Mateusz Bezkorowajny
'''

import sys
import gevent
import _socket
from gevent.socket import socket
from gevent.socket import create_connection
from gevent.socket import tcp_listener
from gevent import monkey
from gevent.ssl import SSLSocket

HOST = '127.0.0.1'
PORT = 1234
#BUFSIZ = 1024
address = (HOST, PORT)
blad = None


def main():  
  gniazdo = None
  try:
    gniazdo = create_connection(address) 
    print 'Udalo sie polaczyc z:', HOST, 'do portu:', PORT
  except _socket.error, blad:
    print 'wystapil blad:' 
    print blad 
  while True:
    msg = gniazdo.recv(1024)  
    print msg #wstepne informacje z serwera
    msg = raw_input() #odpowiedz od uzyszkodnika
    print 'wyslales ', msg
    gniazdo.send(msg)
    msg = gniazdo.recv(1024)
    print msg
    if msg:          
        msg = raw_input()
        gniazdo.send(msg)
        continue
    else:
        print 'Zakonczyles polaczenie z serwerem.'
        break

if __name__ == '__main__':
  sys.exit(main())



