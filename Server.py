'''
Program Server
do wymiany danych medycznych z uzyciem standardu HL7
w ramach projektu SWOP
oraz pracy inzynierskiej
Mateusz Bezkorowajny
'''
import gevent
from gevent.server import StreamServer
from gevent.pool import Pool
import hl7

pacjent = None
global n
n = 0
komunikat1 = 'Wybierz pacjenta, ktorego dane chcesz otrzymac:'
komunikat2 = 'Dane zostaly wyslane'
menu = '''\n
    Dostepne opcje:\n
    0 - Wyjscie\n
    1 - Dodaj dane pacjenta\n
    2 - Pobierz dane pacjenta\n
    3 - Pokaz liste pacjentow\n
    
    Twoj wybor to: '''

#obsluga polaczenia
def obsluga(socket, address):
    print ('Nowe polaczenie z %s:%s' % address)
    while True:
        try:
          socket.send(menu)
          co_robimy = int(socket.recv(1024))
        except:
            print "Nie udalo sie skomunikowac z klientem" 
        if not co_robimy:
            print ("klient zostal rozlaczony\n")
            break
        if co_robimy == 0:
            try:
                socket.send("Zakonczyles polaczenie z serwerem\n")
                socket.send(None)
                print ("klient sie rozlaczyl\n")
            except:
                print "nie udalo sie rozlaczyc!"
                socket.send("Nie udalo sie rozlaczyc.")
                continue
            break
        if co_robimy == 1:
            try:
              socket.send('Podaj dane do wyslania\n')
              dane = ''
              dane += socket.recv(4096)#nie wiem jakie duze beda te dane
            except:
              print "Nie udalo sie odebrac danych hl7"
              socket.send('nie udalo sie odebrac danych hl7')
              continue
            sparsowane = 0
            try:
              sparsowane = hl7.parse(dane) #i to trzeba wrzucic do Mongo jeszcze
              msh = hl7.segment('MSH', sparsowane) #w takiej postaci
              pid = hl7.segment('PID', sparsowane) #ale na szczescie tylko te, ktore beda uzyteczne z punktu widzenia projektu
              obr = hl7.segment('OBR', sparsowane)
              obx = hl7.segment('OBX', sparsowane)
              nk1 = hl7.segment('NK1', sparsowane)
              pv1 = hl7.segment('PV1', sparsowane)
              #i okolo 120 pozostalych...
            except:
              print "Nie udalo sie sparsowac danych"
              socket.send('Nie udalo sie sparsowac danych. Sprawdz czy dane sa na pewno w standardzie hl7')
              continue
          
#            if sparsowane !=0:
 #             try:
  #              if n == 0:
   #               pacjent[0]=sparsowane
    #            else:
     #             n = n+1
      #            pacjent[n]=sparsowane
       #       except:
        #        print "Nie udalo sie zapisac danych pacjenta!"
         #       continue'''
            continue
        if co_robimy == 2:
            try:
                try:
                    socket.send(komunikat1)
                    identyfikator = socket.recv(1024) #pobieramy identyfikator pacjenta
                except:
                    print "Nie udalo sie pobrac identyfikatora pacjenta"
                    continue
                try:
                    socket.send('Wybrales pacjenta o identyfikatorze: ') 
                    socket.send(identyfikator)
                    if not pacjent[identyfikator] or pacjent[identyfikator] == None:
                        print "Nieprawidlowy identyfikator, lub brak pacjenta w bazie! Sprawdz liste pacjentow."
                    else:
                        try:
                            socket.send(pacjent[identyfikator])
                            socket.send(komunikat2)
                        except:
                            print "Nie udalo sie wyslac danych pacjenta!"
                except:
                    print "Nie udalo sie dopasowac i wyslac danych pacjenta"
            except:
                print "Cos sie popsulo..."
            continue
        if co_robimy == 3:
            try:
                socket.send('Lista pacjentow: \n')
                i = 0
                while i < n:
                    socket.send(pacjent[i])
                    i = i+1
            except:
                print "Nie udalo sie wyslac listy pacjentow!"
        else:
            socket.send('Nieprawidlowe polecenie!\n')
            #socket.send(menu)
            continue
        print ("otrzymalem dane\n")
        
if __name__ == '__main__': 
  pool = Pool(5) # do not accept more than 5 connections
  server = StreamServer(('127.0.0.1', 1234), obsluga, spawn=pool) # creates a new server
  print 'Serwer ruszyl!'
  server.serve_forever() # start accepting new connections


