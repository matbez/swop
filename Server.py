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
    ilosc_segmentow=len(sparsowane)
    #msh = hl7.segment('MSH', sparsowane) #Naglowek wiadomosci - nie zawiera przydatnych dla projektu inf.
    pid = hl7.segment('PID', sparsowane) #Informacje o pacjencie
    #Obrobka danych zawartych w polu PID:
    #---------------Data urodzenia:
    if str(pid[7]) == '':
        data = "brak danych"
    else:
        try:
            data_urodzenia = str(pid[7])
            rok = data_urodzenia[0:4]
            miesiac = data_urodzenia[4:6]
            dzien = data_urodzenia[6:8]
            data = dzien + '.' + miesiac + '.' + rok
        except:
            data = "Brak poprawnych danych"
    #---------------Plec:
    if str(pid[8]) == '':
        plec = "brak danych"
    else:
        if str(pid[8]) == "F": 
            plec = 'kobieta'
        if str(pid[8]) == "M": 
            plec = 'mezczyzna'
        if str(pid[8]) == "O": 
            plec = 'inna'
        if str(pid[8]) == "U": 
            plec = 'nieznana'
    #---------------Adres:
    if str(pid[11]) == '':
        adres = 'brak danych'
    else:
        try:
            ulica_nr_domu = str(pid[11][0])
        except:
            ulica_nr_domu = 'nieznane'
        try:
            miasto = str(pid[11][2])
        except:
            miasto = 'nieznane'
        try:
            kod_pocztowy = str(pid[11][4])
        except:
            kod_pocztowy = 'nieznany'
        try:
            wojewodztwo = str(pid[11][3])
        except:
            wojewodztwo = 'nieznane'
        try:
            kraj = str(pid[11][5])
        except:
            kraj = 'nieznany'
        adres = 'Ulica i nr domu: ' + ulica_nr_domu + '\nKod pocztowy: ' + kod_pocztowy + '\nMiasto: ' 
        adres += miasto + '\nWojewodztwo: ' + wojewodztwo + '\nKraj: ' + kraj
    #---------------Telefon domowy/sluzbowy:
    try:
        if str(pid[13]) == '':
            tel_domowy = 'brak danych '
        else:
            tel_domowy = str(pid[13])
    except:
        tel_domowy = 'brak danych '
    try:
        if str(pid[14]) == '':
            tel_sluzbowy = 'brak danych '
        else:
            tel_sluzbowy = str(pid[14])
    except:
        tel_sluzbowy = 'brak danych'
    telefon = "Telefon domowy: " + tel_domowy + " Telefon sluzbowy: " + tel_sluzbowy
    #---------------Stan cywilny:
    try:
        if str(pid[16]) == '':
            stan_cywilny = 'brak danych'
        else:
            if str(pid[16]) == 'D':
                stan_cywilny = 'Rozwiedziony(a)'
            if str(pid[16]) == 'M':
                stan_cywilny = 'Mezata/zonaty'
            if str(pid[16]) == 'S':
                stan_cywilny = 'Samotny(a)'
            if str(pid[16]) == 'U':
                stan_cywilny = 'Nieznany'
            if str(pid[16]) == 'W':
                stan_cywilny = 'Wdowa/wdowiec'
            if str(pid[16]) == 'X':
                stan_cywilny = 'W separacji'
    except:
        stan_cywilny = 'brak danych'
    #---------------Mijesce urodzenia:
    try:        
        if str(pid[23]) == '':
            urodzony = 'brak danych'
        else: 
            urodzony = str(pid[23])
    except:
        urodzony = 'brak danych'
    #---------------Obywatelstwo:
    try:
        if str(pid[23]) == '':
            obywatelstwo = 'brak danych'
        else:
            obywatelstwo = pid[23]
    except:
        obywatelstwo = 'brak danych'
    al1 = hl7.segment('AL1', sparsowane) #alergie
    if al1 != None:
        #Obrobka danych zaqwartych w polu AL1
        i=0
        alergia = 'Alergie pacjenta: \n'
        while i < ilosc_segmentow:
            segment=str(sparsowane[i])
            nazwa=segment[0:3]
            if nazwa == 'AL1':
                id=str(sparsowane[i][1])
                if id == '':
                    id = 1
    #---------------Typ alergii    
                if str(sparsowane[i][2]) == '':
                    typ = 'brak danych'
                else:
                    try:
                        if str(sparsowane[i][2]) == 'DA':
                            typ = 'Alergia na lekarstwa'
                        if str(sparsowane[i][2]) == 'FA':
                            typ = 'Alergia na jedzenie'
                        if str(sparsowane[i][2]) == 'MA':
                            typ = 'Rozne alergie'
                        if str(sparsowane[i][2]) == 'MC':
                            typ = 'Rozne przeciwwskazania'
                        if str(sparsowane[i][2]) == 'EA':
                            typ = 'Alergia srodowiskowe'
                        if str(sparsowane[i][2]) == 'AA':
                            typ = 'Alergia na zwierzeta'
                        if str(sparsowane[i][2]) == 'PA':
                            typ = 'Alergia na rosliwy'
                        if str(sparsowane[i][2]) == 'LA':
                            typ = 'Alergia na pylki'
                    except:
                        typ = 'brak danych'
    #---------------Alergen:
                if str(sparsowane[i][3]) == '':
                    alergen = 'brak danych'
                else:
                    alergen = str(sparsowane[i][3])
    #---------------Stopien zagrozenia dla pacjenta:
                if str(sparsowane[i][4]) == '':
                    zagrozenie = 'brak danych'
                else:
                    if str(sparsowane[i][4]) == 'SV':
                        zagrozenie = 'Poważne'
                    if str(sparsowane[i][4]) == 'MO':
                        zagrozenie = 'Umiarkowane'
                    if str(sparsowane[i][4]) == 'MI':
                        zagrozenie = 'Lagodne'
                    if str(sparsowane[i][4]) == 'U':
                        zagrozenie = 'Nieznane'    
    #---------------Reakcja alergiczna:
                if str(sparsowane[i][5]) == '':
                    reakcja = 'brak danych'
                else:
                    reakcja = str(sparsowane[i][5])
                alergia +='Typ: ' + typ + '\nAlergen: ' + alergen + '\nStopien zagrozenia dla pacjenta: ' + zagrozenie + '\nReakcje alergiczne: ' + reakcja + '\n\n'
            i=i+1 
    else:
        alergia = "Brak danych o alergiach"
    if alergia == 'Alergie pacjenta: \n':
        alergia += "Brak danych o alergiach pacjenta"
    obr = hl7.segment('OBR', sparsowane) #zlecone obserwacje
    if obr != None:
        #Obrobka danych zaqwartych w polu OBR
        i=0
        obserwacje_zlec = 'Zlecone obserwacje u pacjenta: '
        while i < ilosc_segmentow:
            segment=str(sparsowane[i])
            nazwa=segment[0:3]
            if nazwa == 'OBR':
                id_obr=str(sparsowane[i][1])
                if id_obr == '':
                    id_obr = 1
    #---------------identyfikator   
                if str(sparsowane[i][4]) == '':
                    typ = 'brak identyfikatora'
                else:
                    try:
                        identyfikator = str(sparsowane[i][4])
                    except:
                        identyfikator = 'brak poprawnego identyfikatora'
    #---------------data i godzina obserwacji
                if str(sparsowane[i][7]) == '':
                    data_obr = 'brak daty i godziny'
                else:
                    try:
                        obr_data = str(sparsowane[i][7])
                        rok = obr_data[0:4]
                        miesiac = obr_data[4:6]
                        dzien = obr_data[6:8]
                        data_obr = dzien + '.' + miesiac + '.' + rok
                        godzina = obr_data[8:10]
                        minut = obr_data[10:12]
                        data_obr += ' godzina: ' + godzina + ':' + minut
                    except:
                        data_obr = "Brak poprawnych danych"
    #---------------Status rezultatu - tabela 0123
                if str(sparsowane[i][25]) == '':
                    status = 'brak danych'
                else:
                    try:
                        if str(sparsowane[i][25]) == 'O':
                            status = 'Otrzymano zlecenie badania. Oczekiwanie na próbkę'
                        if str(sparsowane[i][25]) == 'I':
                            status = 'Brak wyniku - w trakcie badań'
                        if str(sparsowane[i][25]) == 'S':
                            status = 'Brak wyniku - procedury zaplanowane'
                        if str(sparsowane[i][25]) == 'A':
                            status = 'Częściowe wyniki'
                        if str(sparsowane[i][25]) == 'P':
                            status = 'Wyniki wstępne, nie ostateczne'
                        if str(sparsowane[i][25]) == 'C':
                            status = 'Korekta wyników'
                        if str(sparsowane[i][25]) == 'R':
                            status = 'Wyniki przechowywane, nie zweryfikowane'
                        if str(sparsowane[i][25]) == 'F':
                            status = 'Ostateczne wyniki - zweryfikowane'
                        if str(sparsowane[i][25]) == 'X':
                            status = 'Brak wyników - badanie anulowane'
                        if str(sparsowane[i][25]) == 'Y':
                            status = 'Brak zlecenia wykonania badania'
                        if str(sparsowane[i][25]) == 'Z':
                            status = 'Brak danych pacjenta'
                    except:
                        status = 'Niepoprawna nazwa statusu!'    
    #---------------Podsumowanie OBR
                obserwacje_zlec +='\n\nIdentyfikator: ' + identyfikator + '\nData obserwacji: ' + data_obr + '\nStatus wyniku obserwacji: ' + status 
                #OBX zawsze po OBR, bo to wyniki zleconych wczesniej obserwacji.
                obx = hl7.segment('OBX', sparsowane) #osobne OBX jako takie bedze niepotrzebne...chyba...
                if obx != None:
                    #Obrobka danych zawartych w polu OBX
                    a=i+1
                    obserwacje_wykon = '\nWykonane obserwacje: \n'
                    segment=str(sparsowane[a])
                    nazwa=segment[0:3]
                    while nazwa == 'OBX':
    #---------------ID
                        id_obx=str(sparsowane[a][1])
                        if id_obx == '':
                            id_obx = '1'
    #---------------Typ danych - tabela 0125
                        if str(sparsowane[a][2]) == '':
                            typ_danych = 'brak danych'
                        else:
                            typ_danych = tabela_0125(str(sparsowane[a][2]))
    #---------------Identyfikator obserwacji
                        if  str(sparsowane[a][3]) == '':
                            obx_identyfikator = 'brak danych'
                        else:
                            obx_identyfikator = str(sparsowane[a][3])
    #---------------Wynik obserwacji
                        if  str(sparsowane[a][5]) == '':
                            obx_wynik = 'brak danych'
                        else:
                            obx_wynik = str(sparsowane[a][5])
    #---------------jednostka
                        if  str(sparsowane[a][6]) == '':
                            obx_jednostka = ''
                        else:
                            obx_jednostka = ' ' + str(sparsowane[a][6])
    #---------------Zakres w jakim powinny sie znajdowac powyzsze wyniki
                        if  str(sparsowane[a][7]) == '':
                            obx_zakres = ''
                        else:
                            obx_zakres = '  Prawidlowe wartosci: ' + str(sparsowane[a][7])
    #---------------Interpretacja wyniku
                        if  str(sparsowane[a][8]) == '':
                            obx_interpretacja = ''
                        else:
                            obx_interpretacja = '  Interpretacja: ' + str(sparsowane[a][8])
    #---------------Status wyniku - tabela 0085
                        if  str(sparsowane[a][11]) == '':
                            obx_status = 'brak danych'
                        else:
                            obx_status = tabela_0085(str(sparsowane[a][11]))
                        obserwacje_wykon += '\nID: ' + id_obx + '\nTyp danych: ' + typ_danych + '\nIdentyfikator obserwacji: ' + obx_identyfikator 
                        obserwacje_wykon += '\nWynik: ' + obx_wynik + obx_jednostka + obx_zakres + obx_interpretacja
                        obserwacje_wykon += '\nStatus wyniku: ' + obx_status
                        a=a+1
                        segment=str(sparsowane[a])
                        nazwa = segment[0:3]
                    if obserwacje_wykon == 'Wykonane obserwacje: \n':
                            obserwacje_wykon += 'Brak wykonanych obserwacji'
                            obserwacje_zlec += obserwacje_wykon
                    else:
                        obserwacje_zlec += obserwacje_wykon
            i=i+1 
    else:
        obserwacje_zlec = "Brak danych o obserwacjach"
    if obserwacje_zlec == 'Zlecone obserwacje u pacjenta: ':
        obserwacje_zlec += "Brak danych o o zlecanych obserwacjach"
    #---------------Zestawienie danych osobowych oraz danych medycznych w slownik:
    pacjent = {     "Imie: ": pid[5][1],
                    "Nazwisko: ": pid[5][0],
                    "Plec: ": plec,
                    "Data urodzenia: ": data,
                    "Adres: ": adres,
                    "Telefon: ": telefon,
                    "Stan cywilny: ": stan_cywilny,
                    "Urodzony: ": urodzony,
                    "Obywatelstwo: ": obywatelstwo,
                    "Alergia: ": alergia,
                    "Badania: ": obserwacje_zlec                    
                    }
    #dg1 = hl7.segment('DG1', sparsowane)
    #pr1 = hl7.segment('PR1', sparsowane)
    #evn = hl7.segment('EVN', sparsowane)
    #mpi = hl7.segment('MPI', sparsowane)
    dodaj_do_bazy(pacjent)
#-----------------------------------------------Tabela 0085-------------------------------------------------------#
def tabela_0085(kod):
    if kod == 'C':
        typ = 'Record coming over is a correction and thus replaces a final result '
        return(typ)
    if kod == 'D':
        typ = 'Deletes the OBX record '
        return(typ)
    if kod == 'F':
        typ = 'Final results. '
        return(typ)
    if kod == 'I':
        typ = 'Specimen in lab. '
        return(typ)
    if kod == 'N':
        typ = 'Not asked '
        return(typ)
    if kod == 'O':
        typ = 'Order detail description only (no result) '
        return(typ)
    if kod == 'P':
        typ = 'Preliminary results '
        return(typ)
    if kod == 'R':
        typ = 'Results entered -- not verified '
        return(typ)
    if kod == 'S':
        typ = 'Partial results. '
        return(typ)
    if kod == 'X':
        typ = 'Results cannot be obtained for this observation '
        return(typ)
    if kod == 'U':
        typ = 'Results status change to final without retransmitting results already sent as preliminary. '
        return(typ)
    if kod == 'W':
        typ = 'Post original as wrong '
        return(typ)
    else:
        typ = 'Niepoprawny typ '
    return(typ)
#-----------------------------------------------Tabela 0123-------------------------------------------------------#
#def tabela_0123(kod):
#    if kod == '':
#        typ = ''
#    else:
#        typ = 'Niepoprawna wartość typu'
#    return(typ)
#-----------------------------------------------Tabela 0125-------------------------------------------------------#
def tabela_0125(kod):
    if kod == 'AD':
        typ = 'Adsress '
        return(typ)
    if kod == 'CNE':
        typ = 'Coded with No Exceptions '
        return(typ)
    if kod == 'CWE':
        typ = 'Coded Entry '
        return(typ)
    if kod == 'CF':
        typ = 'Coded Element With Formatted Values '
        return(typ)
    if kod == 'CK':
        typ = 'Composite ID With Check Digit '
        return(typ)
    if kod == 'CN':
        typ = 'Composite ID And Name '
        return(typ)
    if kod == 'CP':
        typ = 'Composite Price '
        return(typ)
    if kod == 'CX':
        typ = 'Extended Composite ID With Check Digit '
        return(typ)
    if kod == 'DR':
        typ = 'Date/Time Range '
        return(typ)
    if kod == 'DT':
        typ = 'Date '
        return(typ)
    if kod == 'DTM':
        typ = 'Time Stamp (Date & Time) '
        return(typ)
    if kod == 'ED':
        typ = 'Encapsulated Data '
        return(typ)
    if kod == 'FT':
        typ = 'Formatted Text (Display) '
        return(typ)
    if kod == 'ID':
        typ = 'Coded Value for HL7 Defined Tables '
        return(typ)
    if kod == 'IS':
        typ = 'Coded Value for User-Defined Tables '
        return(typ)
    if kod == 'MA':
        typ = 'Multiplexed Array '
        return(typ)
    if kod == 'MO':
        typ = 'Money '
        return(typ)
    if kod == 'NA':
        typ = 'Numeric Array '
        return(typ)
    if kod == 'NM':
        typ = 'Numeric '
        return(typ)
    if kod == 'PN':
        typ = 'Person Name '
        return(typ)
    if kod == 'RP':
        typ = 'Reference Pointer '
        return(typ)
    if kod == 'SN':
        typ = 'Structured Numeric '
        return(typ)
    if kod == 'ST':
        typ = 'String Data. '
        return(typ)
    if kod == 'TM':
        typ = 'Time '
        return(typ)
    if kod == 'TN':
        typ = 'Telephone Number '
        return(typ)
    if kod == 'TX':
        typ = 'Text Data (Display)'
        return(typ)
    if kod == 'XAD':
        typ = 'Extended Address '
        return(typ)
    if kod == 'XCN':
        typ = 'Extended Composite Name And Number For Persons '
        return(typ)
    if kod == 'XON':
        typ = 'Extended Composite Name And Number For Organizations '
        return(typ)
    if kod == 'XPN':
        typ = 'Extended Person Name '
        return(typ)
    if kod == 'XTN':
        typ = 'Extended Telecommunications Number '
        return(typ)
    else:
        typ = 'Niepoprawny typ'
    return(typ)
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
            lista = 'Dane pacjenta: \n\n'
            i = 0
            for item in db.pacjenci.find():
                i = i+1
                if numer == i:
                    lista += "\nDane osobowe:\n"
                    lista += 'Imie: ' + item["Imie: "] + '\nNazwisko: ' + item["Nazwisko: "] 
                    lista += '\nPlec: ' + item["Plec: "] + '\nData urodzenia: ' + item["Data urodzenia: "]
                    lista += '\nAdres:\n' + item["Adres: "] + '\n' + item["Telefon: "] + '\nStan cywilny: ' + item["Stan cywilny: "]
                    lista += '\nMiejsce urodzenia: ' + item["Urodzony: "] + '\nObywatelstwo: ' + item["Obywatelstwo: "]
                    lista += '\n\nDane Medyczne:\n'
                    lista += item["Alergia: "] + '\n'
                    lista += item["Badania: "] + '\n'
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
        server = StreamServer(('127.0.0.1', 1234), obsluga, spawn=pool,
                              keyfile='ca-key.pem', certfile='ca-cert.pem', ssl_version=2) #ograniczenie ilosci polaczen
        print 'Serwer ruszyl!'
        server.serve_forever() # start accepting new connections
    except:
        print "Nie udało się wystartować serwera!"
        exit(2)