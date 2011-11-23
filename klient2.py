# -*- coding: utf-8 -*-
'''
Program Klient
do wymiany danych medycznych z uzyciem standardu HL7
w ramach projektu SWOP
oraz pracy inzynierskiej
Mateusz Bezkorowajny
'''
import sys
import _socket
from gevent.socket import socket
from gevent.socket import create_connection
from gevent.ssl import SSLSocket

HOST = '127.0.0.1'
PORT = 1234
address = (HOST, PORT)
blad = None

def wprowadz_dane():
    n='0'
    dane=raw_input() + '\r'
    while True:
        n = raw_input() + '\r'
        if n == '\r':
            return(dane)
        else:
            dane+= n
        
def wyslij_dane(socket, dane):
    dlugosc=str(len(dane))
    socket.send(dlugosc)
    ack=socket.recv(3)
    ack = int(ack)
    if ack == 1:
        socket.send(dane)
    else:
        print "Mamy problem - serwer nie odpowiada na wiadomosc o dlugosci danych!"
        
def odbierz_dane(socket):
    rozmiar = int(socket.recv(1024))
    if rozmiar != 0:
        socket.send("1")
        dane = socket.recv(rozmiar)
        return(dane)
    else:
        socket.send("0")
        print "Problem z odbiorem danych!"

def main():
    socket = None
    try:
        socket = create_connection(address)
        print 'Udalo sie polaczyc z:', HOST, 'do portu:', PORT
    except _socket.error, blad:
        print 'wystapil blad:' 
        print blad 
    while True:
        try:
            dane=odbierz_dane(socket)
            print dane
            #Klient odpowiada:
            dane = wprowadz_dane()
            wyslij_dane(socket, dane)
        except:
            print "Polaczenie zostalo zerwane!"   
            break 
    
if __name__ == '__main__':
    sys.exit(main())