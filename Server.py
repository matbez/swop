# -*- coding: utf-8 -*-
'''
Program Server
do wymiany danych medycznych z uzyciem standardu HL7
w ramach projektu SWOP
oraz pracy inzynierskiej
Mateusz Bezkorowajny
'''
from gevent.server import StreamServer
from gevent.pool import Pool
import hl7
from pymongo.connection import Connection
from pymongo import ASCENDING
import json

#-------------------------------------------------Zmienne Globalne-----------------------------------------------#
menu = '''\n
    Dostepne opcje:\n
    9 - Wyjscie\n
    1 - Dodaj dane pacjenta\n
    2 - Pobierz dane pacjenta\n
    3 - Pokaz liste pacjentow\n
    
    Zatwierdzenie danych do wyslania odbywa sie poprzez wyslanie pustej linii.
    
    Twoj wybor to: '''
    
identyfikator = []
licznik = []

#----------------------------------------------------Parsowanie--------------------------------------------------#
def parsowanie(dane, licznik):
    sparsowane = hl7.parse(dane)
    msh = hl7.segment('MSH', sparsowane) #w takiej postaci
    pid = hl7.segment('PID', sparsowane) #ale na szczescie tylko te, ktore beda uzyteczne z punktu widzenia projektu
    obr = hl7.segment('OBR', sparsowane)
    obx = hl7.segment('OBX', sparsowane)
    nk1 = hl7.segment('NK1', sparsowane)
    pv1 = hl7.segment('PV1', sparsowane)
    #tu bedzie jeszcze 120 innych...
    #a potem odwolanie do funkcji zapisujacej to do bazy danych
    
    #wybiorcze sprawdzenie czy wszystko dziala:
    print sparsowane
    print
    print nk1
    print pid
    
    pacjent = {"MSH: ": msh, #tu beda tylko te pola, ktore przydadza sie z punktu widzenia projektu.
               "PID: ": pid, #Ew. do bazy zostana wyslane juz tylko istotne dane wyciagniete z parsera
               "OBR: ": obr, #pewnie okaze sie jak dostane i ogarne standardy
               "OBX: ": obx,
               "NK1: ": nk1,
               "PV1: ": pv1}
    dodaj_do_bazy(pacjent, licznik)

#-----------------------------------------------Dodawanie do Bazy-------------------------------------------------#
def dodaj_do_bazy(pacjent, liczik):
    dodaj  = db.pacjenci
    identyfikator[licznik] = dodaj.insert(pacjent)

#-----------------------------------------------Wypisywanie z Bazy------------------------------------------------#
def wypisz_z_bazy():
    cursor = db.pacjenci.find()
    j=db.pacjenci.count()
    lista=None
    i = 0
    while i <= j :
        lista = cursor[i] #W planie bylo lista += ... ale to nie ma prawa bytu 
        print lista #Tu sprawdzalem czy mi sie w ogole cos udalo wyciagnac z cursora
        i=i+1
    return(lista) 
    #db.pacjenci.find({"$oid":licznik[numer]}) - wyszukiwanie jednego pacjenta? Śmieć! Niedokończony pomysł - raczej do wywalenia to będzie
    
#-----------------------------------------------Wprowadzanie danych-----------------------------------------------#
def wprowadz_dane():
    n='0'
    dane=raw_input() + '\r'
    while True:
        n = raw_input() + '\r'
        if n == '\r':
            return(dane)
        else:
            dane+= n
#----------------------------------------------Wysylanie danych---------------------------------------------------#     
def wyslij_dane(socket, dane):
    dlugosc=str(len(dane))
    socket.send(dlugosc)
    ack=socket.recv(3)
    ack = int(ack)
    if ack == 1:
        socket.send(dane)
    else:
        print "Mamy problem - klient nie odpowiada na wiadomosc o dlugosci danych!"
#-----------------------------------------------Odbieranie danych--------------------------------------------------#        
def odbierz_dane(socket):
    rozmiar = int(socket.recv(1024))
    if rozmiar != 0:
        socket.send("1")
        dane = socket.recv(rozmiar)
        return(dane)
    else:
        socket.send("0")
        print "Problem z odbiorem danych!"
#-----------------------------------------------Obsluga polaczenia-------------------------------------------------#
def obsluga(socket, address):
    print ('Nowe polaczenie z %s:%s' % address)
    dane = menu
    while True:
        try:
            wyslij_dane(socket, dane)
            co_robimy = int(odbierz_dane(socket))
            print co_robimy
        except:
            print "Nie udalo sie skomunikowac z klientem" 
        if not co_robimy:
            print ("klient zostal rozlaczony\n")
            break
        if co_robimy == 9:
            try:
                komunikat_rozlacz = "Zakonczyles polaczenie z serwerem\n"
                wyslij_dane(socket, komunikat_rozlacz)
                print ("klient sie rozlaczyl\n")
            except:
                print "nie udalo sie rozlaczyc!"
                komunikat_rozlacz_err = "Nie udalo sie rozlaczyc."
                wyslij_dane(socket, komunikat_rozlacz_err)
                continue
            break
        if co_robimy == 1:
            try:
                #licznik = licznik + 1 #to w celu identyfikacji pacjentow w kolejnosci dodawania - chwilowe i nie skonczone rozwiazanie
                komunikat_dodaj_1 = "Wprowadz dane pacjenta: "
                wyslij_dane(socket, komunikat_dodaj_1)
                pacjent = odbierz_dane(socket)
                try:
                    parsowanie(pacjent, licznik)
                except:
                    print "nie udalo sie sparsowac danych!"
            except:
                print "cos poszlo nie tak, przy odbieraniu danych pacjenta"
        if co_robimy == 2:
            try:
                komunikat_wyslij_1 = "Podaj identyfikator pacjenta, ktorego dane chcesz otrzymac: "
                wyslij_dane(socket, komunikat_wyslij_1)
                pacjent = odbierz_dane(socket)
                #db.pacjenci.find_one(licznik[pacjent])
                #w tym miejscu bedze trzeba zrobic odczyt z bazy danych odpowiedniego pacjenta i wysylanie jego danych
            except:
                print "Cos sie popsulo - nie da sie odczytac danych pacjenta!"
        if co_robimy == 3:
            komunikat_lista_1 = "Lista pacjentow: "
            lista =  wypisz_z_bazy()
            dane = komunikat_lista_1 + '\n' + lista + '\n' + menu
        else:
            print "Klient podal zly identyfikator"
            print co_robimy
#------------------------------------------------------------------------------------------------------------------#    
    
if __name__ == '__main__': 
    licznik = 0
    # polaczenie baza danych
    connection = Connection("localhost", 27017)
    #Wybranie bazy danych pacjenci
    db = connection.pacjenci
    pool = Pool(5) # do not accept more than 5 connections
    server = StreamServer(('127.0.0.1', 1234), obsluga, spawn=pool) # creates a new server
    print 'Serwer ruszyl!'
    server.serve_forever() # start accepting new connections
