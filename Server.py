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
#from xml.dom.minidom import parse, parseString #do parsowania HL7 v3.x (czyli xml)
#---------------------------------------------------Definicja menu-----------------------------------------------#
menu = '''\n
    Dostepne opcje:\n
    0 - Wyjscie\n
    1 - Dodaj dane pacjenta\n
    2 - Pobierz dane pacjenta\n
    3 - Pokaz liste pacjentow\n
    
    Zatwierdzenie danych do wyslania odbywa sie poprzez wyslanie pustej linii.
    
    Twoj wybor to: '''
#------------------------------------------------Parsowanie HL7 v2.x----------------------------------------------#
def parsowanie(dane):
    sparsowane = hl7.parse(dane)
    msh = hl7.segment('MSH', sparsowane) #w takiej postaci
    pid = hl7.segment('PID', sparsowane) #ale na szczescie tylko te, ktore beda uzyteczne z punktu widzenia projektu
    obr = hl7.segment('OBR', sparsowane)
    obx = hl7.segment('OBX', sparsowane)
    nk1 = hl7.segment('NK1', sparsowane)
    pv1 = hl7.segment('PV1', sparsowane)
    al1 = hl7.segment('AL1', sparsowane)
    dg1 = hl7.segment('DG1', sparsowane)
    pr1 = hl7.segment('PR1', sparsowane)
    evn = hl7.segment('EVN', sparsowane)
    mpi = hl7.segment('MPI', sparsowane)
    #tu bedzie jeszcze 120 innych...
    
    pacjent = {"Imie: ": pid[5][1],
               "Nazwisko: ": pid[5][0],       
               "MSH: ": msh, #tu beda tylko te pola, ktore przydadza sie z punktu widzenia projektu.
               "PID: ": pid, #Ew. do bazy zostana wyslane juz tylko istotne dane wyciagniete z parsera (jak imie i nazwisko wyzej)
               "OBR: ": obr, 
               "OBX: ": obx, #PROBLEM!! Niektore pola mogawystepowac >1 razy !!! Wtedy tracimy tu dane! (chociaz sie parsuja wczesniej)
               "NK1: ": nk1,
               "PV1: ": pv1,
               "AL1: ": al1,
               "DG1: ": dg1,
               "PR1: ": pr1,
               "EVN: ": evn,
               "MPI: ": mpi }
    
    dodaj_do_bazy(pacjent)
#-----------------------------------------------Parsowanie HL7 v 3.x ---------------------------------------------#
#def parsowanie_v3(dane):
#sparsowane = parseString(dane)
#-----------------------------------------------Dodawanie do Bazy-------------------------------------------------#
def dodaj_do_bazy(pacjent):
    dodaj  = db.pacjenci
    _id = dodaj.insert(pacjent)
#-----------------------------------------------Wypisywanie z Bazy------------------------------------------------#
def wypisz_z_bazy():
    lista =''
    i = 0
    for item in db.pacjenci.find():
        i = i+1
        lista += str(i) + '. ' + item["Imie: "] + ' ' + item["Nazwisko: "] + '\n'
    #print lista
    return(lista)    
#-----------------------------------------------Wyszukiwanie w Bazie----------------------------------------------#
def szukaj_w_bazie(numer):
    j=db.pacjenci.count() 
    if numer <= j:
            lista = 'Dane pacjenta: \n'
            cursor = db.pacjenci.find()
            i = 0
            for item in db.pacjenci.find():
                i = i+1
                if numer == i:
                    lista += str(i) + '. ' + item["Imie: "] + ' ' + item["Nazwisko: "] + '\n' 
            lista += repr(cursor[numer-1])
    else:
        lista = 'Nieprawidłowy numer pacjenta! Sprawdz liste pacjentow.'
    return(lista)    
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
            dane = menu
            co_robimy = odbierz_dane(socket)
        except:
            print "Nie udalo sie skomunikowac z klientem" 
        if not co_robimy:
            print ("klient zostal rozlaczony\n")
            break
        if co_robimy == "0\r":
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
        if co_robimy == "1\r":
            try:
                komunikat_dodaj_1 = "Wprowadz dane pacjenta: "
                wyslij_dane(socket, komunikat_dodaj_1)
                pacjent = odbierz_dane(socket)
                if pacjent[0:9] == 'MSH|^~\&|' : #w ten sposob mozna tez sprawdzic czy to HL7v2.x czy HL7v3.x i wybrac odpowiedni parser
                    try:
                        parsowanie(pacjent)
                        dane = 'Dane pacjenta zapisane!' + menu
                    except:
                        print "nie udalo sie sparsowac danych!"
                        dane = 'wystapil blad przy parsowaniu danych. Sprobuj jeszcze raz.' + menu
                else:
                    print "dane nie są w hl7!"
                    dane = "Podane danie nie są zgodne ze standardem HL7! \n\n" + menu
            except:
                print "cos poszlo nie tak, przy odbieraniu danych pacjenta"
        if co_robimy == "2\r":
            try:
                komunikat_wyslij_1 = "Podaj identyfikator pacjenta, ktorego dane chcesz otrzymac: "
                wyslij_dane(socket, komunikat_wyslij_1)
                pacjent = int(odbierz_dane(socket))
                dane_pacjenta = szukaj_w_bazie(pacjent)
                dane = dane_pacjenta + '\n\n' + menu
            except:
                print "Cos sie popsulo - nie da sie odczytac danych pacjenta!"
        if co_robimy == "3\r":
            komunikat_lista_1 = "Lista pacjentow: \n"
            lista =  wypisz_z_bazy()
            dane = komunikat_lista_1 + '\n' + lista + '\n' + menu
        if dane == menu:
            dane = "Nieprawidlowy wybor! Podaj jeszcze raz, co chcesz zrobic.\n\n" + menu
#------------------------------------------------------------------------------------------------------------------#    
if __name__ == '__main__': 
    # polaczenie baza danych
    try:
        connection = Connection("localhost", 27017)
    except:
        print 'Baza danych nie jest uruchomiona!'
        exit(1)
    #Wybranie bazy danych pacjenci
    db = connection.pacjenci
    print 'Polaczono sie z baza danych!'
    pool = Pool(3) # do not accept more than 3 connections
    try:
        server = StreamServer(('127.0.0.1', 1234), obsluga, spawn=pool) #ograniczenie ilosci polaczen
        print 'Serwer ruszyl!'
        server.serve_forever() # start accepting new connections
    except:
        print "Nie udało się wystartować serwera!"
        exit(2)