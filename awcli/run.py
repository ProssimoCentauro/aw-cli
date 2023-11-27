import os
import sys
import argparse
import warnings
import csv
import concurrent.futures
from pySmartDL import SmartDL
from pathlib import Path
from threading import Thread
from awcli.utilities import *  

if nome_os == "Windows":
    from windows import *

def safeExit():
    with open(f"{os.path.dirname(__file__)}/aw-cronologia.csv", 'w', newline='', encoding='utf-8') as file:
        csv.writer(file).writerows(log)
    exit()


def RicercaAnime() -> list[Anime]:
    """
    Dato in input un nome di un anime inserito dall'utente, restituisce una lista con gli URL degli anime
    relativi alla ricerca.

    Returns:
        list[Anime]: la lista con gli URL degli anime trovati
    """

    def check_search(s: str):
        if s == "exit":
            safeExit() 
        result = search(s, nome_os)
        if len(result) != 0:
            return result

    my_print("", end="", cls=True)
    return my_input("Cerca un anime", check_search,"La ricerca non ha prodotto risultati", cls = True)


def animeScaricati(path: str) -> list[Anime]:
    """
    Prende i nomi degli anime scaricati nella cartella Video/Anime.

    Args:
        path (str): il path relativo alla cartella Video/Anime

    Returns:
        list[Anime]: la lista degli anime trovati
    """
    nomi = os.listdir(path)

    if len(nomi) == 0:
        my_print("Nessun anime scaricato", color='rosso')
        safeExit()

    animes = list[Anime]()
    for name in nomi:
        animes.append(Anime(name, f"{path}/{name}"))
    return animes


def scegliEpisodi() -> tuple[int, int]:
    """
    Fa scegliere all'utente gli episodi dell'anime da guardare.

    Se l'anime ha solo un episodio, questo verrà riprodotto automaticamente.
    In caso contrario, l'utente può scegliere un singolo episodio o un intervallo di episodi da riprodurre.
    Inserire il valore predefinito (Enter) farà riprodurre tutti gli episodi disponibili.

    Returns:
        tuple[int, int]: una tupla con il numero di episodio iniziale e finale da riprodurre.
    """

    
    my_print(anime.name, cls=True)
    #se contiene solo 1 ep sarà riprodotto automaticamente
    if anime.ep == 1:
        return 1, 1

    # faccio decire all'utente il range di ep
    if (nome_os == "Android"):
        my_print("Attenzione! Su Android non è ancora possibile specificare un range per lo streaming", color="giallo")
    # controllo se l'utente ha inserito un range o un episodio unico
    def check_string(s: str):
        if s.isdigit():
            n = int(s)
            if n in range(anime.ep_ini, anime.ep+1):
                return n,n
        elif "-" in s:
            n, m = s.split("-")
            if not n.isdigit() or not m.isdigit():
                return None
            n = int(n)
            m = int(m)
            if n in range(anime.ep_ini, anime.ep+1) and m in range(n, anime.ep+1):
                return n, m
        elif s == "":
            return anime.ep_ini, anime.ep

    return my_input(f"Specifica un episodio, o per un range usa: ep_iniziale-ep_finale (Episodi: {anime.ep_ini}-{anime.ep})",check_string,"Ep. o range selezionato non valido")


def downloadPath(create: bool = True) -> str:
    """
    Restituisce il percorso di download dell'anime, a seconda del sistema operativo in uso.
    Se create è True (valore predefinito) e il percorso non esiste, viene creato.

    Args:
        create (bool, optional): se impostato a True, crea il percorso se non esiste. Valore predefinito: True.

    Returns:
        str: il percorso di download dell'anime.
    """

    if (nome_os == "Android"):
        path = f"/sdcard/Movies/Anime"
    else:
        path = f"{Path.home()}/Videos/Anime"
    if create and not os.path.exists(path):
        os.makedirs(path)
    return path


def scaricaEpisodio(ep: int, path: str):
    """
    Scarica l'episodio dell'anime e lo salva nella cartella specificata.
    Se l'episodio è già presente nella cartella, non viene riscaricato.

    Args:
        ep (int): il numero dell'episodio da scaricare.
        path (str): il percorso dove salvare l'episodio.
    """

    url_ep = anime.get_episodio(ep)
    nome_video = anime.ep_name(ep)
    
    # se l'episodio non è ancora stato scaricato lo scarico, altrimenti skippo
    my_print(nome_video, color="blu", end=":\n")
    if not os.path.exists(f"{path}/{nome_video}.mp4"):
        SDL = SmartDL(url_ep, f"{path}/{nome_video}.mp4")
        SDL.start()
    else:
        my_print("già scaricato, skippo...", color="giallo")


def openSyncplay(url_ep: str, nome_video: str):
    """
    Avvia Syncplay.

    Args:
        url_ep (str): l'URL dell'episodio da riprodurre.
        nome_video (str): il nome dell'episodio.
    """

    if syncplay_path == "Syncplay: None":
        my_print("Aggiornare il path di syncplay nella configurazione tramite: aw-cli -a", color="rosso")
        safeExit()

    comando = f''''{syncplay_path}' "{url_ep}" media-title="{nome_video}"'''
    if nome_os == "Windows":
        warnings.filterwarnings("ignore", category=UserWarning)
        winOpen("Syncplay.exe", f"& {comando}")
    else:
        os.system(f"{comando} --language it &>/dev/null")


def openMPV(url_ep: str, nome_video: str):
    """
    Apre MPV per riprodurre il video.

    Args:
        url_server (str): il link del video o il percorso del file.
        nome_video (str): il nome del video.
    """


    if (nome_os == "Android"):
        os.system(f'''am start --user 0 -a android.intent.action.VIEW -d "{url_ep}" -n is.xyz.mpv/.MPVActivity > /dev/null 2>&1 &''')
        return
    
    comando = f"""'{player_path}' "{url_ep}" --force-media-title="{nome_video}" --fullscreen --keep-open"""
    if nome_os == "Windows":
        winOpen("mpv.exe", f"""& {comando}""")
    else:
        os.system(f'''{comando} &>/dev/null''')


def openVLC(url_ep: str, nome_video: str):
    """
    Apre VLC per riprodurre il video.

    Args:
        url_server (str): il link del video o il percorso del file.
        nome_video (str): il nome del video.
    """

    if nome_os == "Android":
        os.system(f'''am start --user 0 -a android.intent.action.VIEW -d "{url_ep}" -n org.videolan.vlc/.StartActivity -e "title" "{nome_video}" > /dev/null 2>&1 &''')    
        return
    
    comando = f''''{player_path}' "{url_ep}" --meta-title "{nome_video}" --fullscreen'''
    if nome_os == "Windows":        
        winOpen("vlc.exe", f"""& {comando} """)
    else:
        os.system(f'''{comando} &>/dev/null''')


def addToCronologia(ep: int):
    """
    Viene aggiunta alla cronologia locale il nome del video,
    il numero dell'ultimo episodio visualizzato,
    il link di AnimeWorld relativo all'anime, 
    il numero reale di episodi totali della serie e lo stato dell'anime.
    La cronologia viene salvata su un file csv nella stessa 
    directory dello script. Se il file non esiste viene creato.

    Args:
        ep (int): il numero dell'episodio visualizzato.
    """
    for i, riga in enumerate(log):
        #se l'anime è presente
        if riga[0] == anime.name:
            #se l'ep riprodotto è l'ultimo allora non lo inserisco più
            if ep == anime.ep and anime.status == 1:
                log.pop(i)
            else: 
                #sovrascrivo la riga   
                log[i][1] = ep
                log[i][2] = anime.url
                log[i][3] = anime.ep_totali
                log[i][4] = anime.status
                log[i][5] = anime.ep
                temp = log.pop(i)
                #se l'anime è in corso e l'ep visualizzato è l'ultimo, metto l'anime alla fine della cronologia
                if anime.status == 0 and ep == anime.ep:
                    log.insert(len(log), temp)
                #altrimenti all'inizio
                else:
                    log.insert(0, temp)
            return
    if (ep == anime.ep and anime.status == 0) or ep != anime.ep:
        if anime.status == 0 and ep == anime.ep:
            log.insert(len(log), [anime.name, ep, anime.url, anime.ep_totali, anime.status, anime.ep])
        else:
            log.insert(0, [anime.name, ep, anime.url, anime.ep_totali, anime.status, anime.ep]) 


def updateAnilist(ratingAnilist: bool, preferitoAnilist: bool,  ep: int, voto_anilist: str):
    """
    Procede ad aggiornare l'anime su AniList.
    Se l'episodio riprodotto è l'ultimo e
    l'utente ha scelto di votare gli anime,
    verrà chiesto il voto da dare.

    Args:
        ratingAnilist (bool): valore impostato a True se l'utente ha scelto di votare l'anime una volta finito, altrimenti False.
        preferitoAnilist(bool): True se l'utente ha scelto di far chiedere se mettere l'anime tra i preferiti, altrimenti False.
        ep (int): il numero dell'episodio visualizzato.
        voto_anilist (str): il voto dato dall'utente all'anime su Anilist.
    """

    voto = 0
    preferiti = False
    status_list = 'CURRENT'
    #se ho finito di vedere l'anime
    if ep == anime.ep and anime.status == 1:
        status_list = 'COMPLETED'
        #chiedo di votare
        if ratingAnilist:
            def is_number(n):
                try:
                    float(n)
                    return float(n)
                except ValueError:
                    pass

            voto = my_input(f"Inserisci un voto per l'anime (voto corrente: {voto_anilist})", is_number)
    
        #chiedo di mettere tra i preferiti
        if preferitoAnilist:
            def check_string(s: str):
                s = s.lower()
                if s == "s":
                    return True
                elif s == "n" or s == "":
                    return False

            preferiti = my_input("Mettere l'anime tra i preferiti? (s/N)", check_string)
    
    thread = Thread(target=anilistApi, args=(anime.id_anilist, ep, voto, status_list, preferiti))
    thread.start()


def openVideos(ep_iniziale: int, ep_finale: int, ratingAnilist: bool, preferitoAnilist: bool, user_id: int):
    """
    Riproduce gli episodi dell'anime, a partire da ep_iniziale fino a ep_finale.
    Se un episodio è già stato scaricato, viene riprodotto dal file scaricato.
    Altrimenti, viene riprodotto in streaming.

    Args:
        ep_iniziale (int): il numero di episodio iniziale da riprodurre.
        ep_finale (int): il numero di episodio finale da riprodurre.
        ratingAnilist (bool): valore impostato a True se l'utente ha scelto di votare l'anime una volta finito, altrimenti False.
        preferitoAnilist(bool): True se l'utente ha scelto di far chiedere se mettere l'anime tra i preferiti, altrimenti False.
    """

    for ep in range(ep_iniziale, ep_finale+1):

        nome_video = anime.ep_name(ep)
        #se il video è già stato scaricato lo riproduco invece di farlo in streaming
        path = f"{downloadPath(create=False)}/{anime.name}/{nome_video}.mp4"
        
        if os.path.exists(path):
            url_server = "file://" + path if nome_os == "Android" else path
        elif offline:
            my_print(f"Episodio {nome_video} non scaricato, skippo...", color='giallo')
            sleep(1)
            continue
        else:
            url_server = anime.get_episodio(ep)

        my_print(f"Riproduco {nome_video}...", color="giallo", cls=True)

        #se è l'episodio finale e l'utente deve votare l'anime, controllo se l'id è presente
        # e ottengo il voto dell'anime se già inserito in precedenza
        #prendo l'id dell'utente tramite query
        voto_anilist = "n.d."
        if ep == anime.ep and anime.status == 1 and ratingAnilist == True and not offline and not privato:         
            #prendo il voto se presente
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_rating = executor.submit(getAnimePrivateRating, user_id, anime.id_anilist)
                voto_anilist = future_rating.result()

        openPlayer(url_server, nome_video)

        #se non sono in modalità offline o privata aggiungo l'anime alla cronologia
        if not offline and not privato:
            addToCronologia(ep)

        #update watchlist anilist se ho fatto l'accesso
        if tokenAnilist != 'tokenAnilist: False' and not offline and not privato:
            updateAnilist(ratingAnilist, preferitoAnilist, ep, voto_anilist)


def getCronologia() -> list[Anime]:
    """
    Prende i dati dalla cronologia.

    Returns:
        list[Anime]: la lista degli anime trovati 

    """
    animes = []
    for riga in log:
        if len(riga) < 4:
            riga.append("??")
        if len(riga) < 5:
            riga.append(0)
        if len(riga) < 6:
            riga.append(riga[1])    
        
        a = Anime(name=riga[0], url=riga[2], ep=int(riga[5]), ep_totali=riga[3])
        a.ep_corrente = int(riga[1])
        a.status = int(riga[4])
        animes.append(a)

    #se il file esiste ma non contiene dati stampo un messaggio di errore
    if len(animes) == 0:
        my_print("Cronologia inesistente!", color='rosso')
        safeExit()
    return animes


def setupConfig() -> None:
    """
    Crea un file di configurazione chiamato "aw.config"
    nella stessa directory dello script.
    Le informazioni riportate saranno scelte dall'utente.
    Sarà possibile scegliere il Player predefinito, 
    se collegare il proprio profilo AniList e 
    se inserire il path di syncplay.  
    """
    try:
        #player predefinito
        my_print("", end="", cls=True)
        my_print("AW-CLI - CONFIGURAZIONE", color="giallo")
        my_print("1", color="verde", end="  ")
        my_print("MPV")
        my_print("2", color="verde", end="  ")
        my_print("VLC")

        def check_index(s: str):
            if s == "1":
                return "mpv" if nome_os == "Linux" else my_input("Inserisci il path del player")
            elif s == "2":
                return "vlc" if nome_os == "Linux" else my_input("Inserisci il path del player")


        player = my_input("Scegli un player predefinito", check_index)

        #animelist
        def check_string(s: str):
            s = s.lower()
            if s == "s":
                return True
            elif s == "n" or s == "":
                return False

        anilist = my_input("Aggiornare automaticamente la watchlist con AniList? (s/N)", check_string)

        if anilist:
            if nome_os == "Linux" or nome_os == "Android":
                os.system("xdg-open 'https://anilist.co/api/v2/oauth/authorize?client_id=11388&response_type=token' &>/dev/null")
            elif nome_os == "Windows":
                Popen(['powershell.exe', "explorer https://anilist.co/api/v2/oauth/authorize?client_id=11388&response_type=token"])
            else: 
                os.system("open 'https://anilist.co/api/v2/oauth/authorize?client_id=11388&response_type=token' &>/dev/null")

            #inserimento token
            global tokenAnilist
            tokenAnilist = my_input("Inserire il token di AniList", cls=True)
            #chiede se votare l'anime
            if my_input("Votare l'anime una volta completato? (s/N)", check_string):
                ratingAnilist = "ratingAnilist: True "
                #prendo l'id dell'utente tramite query
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(getAnilistUserId, tokenAnilist)
                    user_id = future.result()
            else:
                ratingAnilist = "ratingAnilist: False"
                user_id = 0
            preferitoAnilist = "preferitoAnilist: True" if my_input("Chiedere se mettere l'anime tra i preferiti una volta completato? (s/N)", check_string) else "preferitoAnilist: False"

        else:
            tokenAnilist = "tokenAnilist: False"
            ratingAnilist = "ratingAnilist: False"
            preferitoAnilist = "preferitoAnilist: False"
            user_id = 0

        if nome_os == "Linux":
            syncplay= "syncplay"
        else:
            syncplay = my_input("Inserisci il path di Syncplay (premere INVIO se non lo si desidera utilizzare)")
            if syncplay == "":
                syncplay = "Syncplay: None"
    except KeyboardInterrupt:
        safeExit()
    #creo il file
    config = f"{os.path.dirname(__file__)}/aw.config"
    with open(config, 'w') as config_file:
        config_file.write(f"{player}\n")
        config_file.write(f"{tokenAnilist}\n")
        config_file.write(f"{ratingAnilist}\n")
        config_file.write(f"{preferitoAnilist}\n")
        config_file.write(f"{user_id}\n")
        config_file.write(f"{syncplay}")


def reloadCrono(cronologia: list[Anime]):
    """
    Aggiorna la cronologia degli anime con le ultime uscite disponibili e la ristampa.

    Questa funzione esamina ciascun anime nella lista `animelist` e verifica se sono disponibili nuove uscite.
    Se trova nuove uscite per un anime, ne aggiorna lo stato.

    Args:
        cronologia (list[Anime]): Una lista Anime in cronologia.

    """
    if 0 not in [anime.status for anime in cronologia]:
        return
    
    my_print("Ricerco le nuove uscite...", color="giallo")
    ultime_uscite = latest()
    my_print(end="", cls=True)
                
    for i, a in reversed(list(enumerate(cronologia))):
        colore = "rosso"
        if a.status == 1 or a.ep_corrente < a.ep:
            colore = "verde"
        else:    
            for anime_latest in ultime_uscite:
                if a.name == anime_latest.name and a.ep_corrente < anime_latest.ep:
                    log[i][5] = anime_latest.ep
                    colore = "verde"
                    break
                
        my_print(f"{i + 1} ", color=colore, end=" ")
        my_print(f"{a.name} [Ep {a.ep_corrente}/{a.ep_totali}]")
        
    my_print("Scegli un anime\n> ", end=" ", color="magenta")


def main():
    global log
    global syncpl
    global downl
    global lista
    global offline
    global cronologia
    global info
    global privato
    global anime
    global player_path
    global syncplay_path
    global openPlayer

    try:
        with open(f"{os.path.dirname(__file__)}/aw-cronologia.csv", encoding='utf-8') as file:
            log = [riga for riga in csv.reader(file)]
    except FileNotFoundError:
        pass
    
    # args
    parser = argparse.ArgumentParser("aw-cli", description="Guarda anime dal terminale e molto altro!")
    parser.add_argument('-a', '--configurazione', action='store_true', dest='avvia_config', help='avvia il menu di configurazione')
    parser.add_argument('-c', '--cronologia', action='store_true', dest='cronologia', help='continua a guardare un anime dalla cronologia')
    parser.add_argument('-d', '--download', action='store_true', dest='download', help='scarica gli episodi che preferisci')
    parser.add_argument('-i', '--info', action='store_true', dest='info', help='visualizza le informazioni e la trama di un anime')
    parser.add_argument('-l', '--lista', nargs='?', choices=['a', 's', 'd', 't'], dest='lista', help="lista degli ultimi anime usciti su AnimeWorld. a = all, s = sub, d = dub, t = tendenze. Default 'a'")
    parser.add_argument('-o', '--offline', action='store_true', dest='offline', help='apri gli episodi scaricati precedentemente direttamente dal terminale')
    parser.add_argument('-p', '--privato', action='store_true', dest='privato', help="guarda un episodio senza che si aggiorni la cronologia o AniList")
    if nome_os != "Android":
        parser.add_argument('-s', '--syncplay', action='store_true', dest='syncpl', help='usa syncplay per guardare un anime insieme ai tuoi amici')
    parser.add_argument('-v', '--versione', action='store_true', dest='versione', help="stampa la versione del programma")
    
    args = parser.parse_args()
    
    if args.avvia_config:
        setupConfig()
    if  '-l' in sys.argv and args.lista == None:
        args.lista = 'a'
    
    #se il file di configurazione non esiste viene chiesto all'utente di fare il setup
    if not os.path.exists(f"{os.path.dirname(__file__)}/aw.config"):
        setupConfig()

    mpv, player_path, ratingAnilist, preferitoAnilist, user_id, syncplay_path = getConfig()
    #se la prima riga del config corrisponde a una versione vecchia, faccio rifare il config
    if player_path == "Player: MPV" or player_path == "Player: VLC" or syncplay_path == None:
        my_print("Ci sono stati dei cambiamenti nella configurazione...", color="giallo")
        sleep(1)
        setupConfig()
        mpv, player_path, ratingAnilist, preferitoAnilist, user_id, syncplay_path = getConfig()

   
    openPlayer = openMPV if mpv else openVLC


    if nome_os != "Android" and args.syncpl:
        openPlayer = openSyncplay
    if args.info:
        info = True
    if args.download:
        downl = True
    if args.lista:
        lista = True
    if args.versione:
        my_print(f"aw-cli versione: {versione}", cls=True)
        safeExit()
    if args.privato:
        privato = True
    elif args.offline:
        offline = True
    elif args.cronologia:
        cronologia = True

    while True:
        try:
            if cronologia:
                animelist = getCronologia()
            elif lista:
                animelist = latest(args.lista)
            elif offline:
                animelist = animeScaricati(downloadPath())
            else:
                animelist = RicercaAnime()
                
            while True:
                my_print("", end="", cls=True)
                # stampo i nomi degli anime
                colore = "verde"
                for i, a in reversed(list(enumerate(animelist))):
                    if cronologia:
                        colore = "rosso"
                        if a.status == 1 or a.ep_corrente < a.ep:
                            colore = "verde"
                    
                    my_print(f"{i + 1} ", color=colore, end=" ")
                    if cronologia:
                        my_print(f"{a.name} [Ep {a.ep_corrente}/{a.ep_totali}]")
                    elif lista:
                       my_print(f"{a.name} [Ep {a.ep}]") 
                    else:
                        my_print(a.name)
                if cronologia:
                    thread = Thread(target=reloadCrono, args=[animelist])    
                    thread.start()

                def check_index(s: str):
                    if s.isdigit():
                        index = int(s) - 1
                        if index in range(len(animelist)):
                            return index
                
                scelta = my_input("Scegli un anime", check_index)
                anime = animelist[scelta]
                #se la lista è stata selezionata, inserisco come ep_iniziale e ep_finale quello scelto dall'utente
                #succcessivamente anime.ep verrà sovrascritto con il numero reale dell'episodio finale
                if lista:
                    ep_iniziale = anime.ep
                    ep_finale = ep_iniziale
                scelta_info = ""
                if info:
                    scelta_info = anime.getAnimeInfo()
                    if scelta_info == 'i':
                        break

                anime.load_episodes() if not offline else anime.downloaded_episodes(f"{downloadPath()}/{anime.name}")

                if anime.ep != 0:
                    break

                # se l'anime non ha episodi non può essere selezionato
                my_print("Eh, volevi! L'anime non è ancora stato rilasciato", color="rosso")
                sleep(1)
            #se ho l'args -i e ho scelto di tornare indietro, faccio una continue sul ciclo while True
            if scelta_info == 'i':
                continue
            if not cronologia:
                if not lista:
                    ep_iniziale, ep_finale = scegliEpisodi()
            else:
                ep_iniziale = anime.ep_corrente + 1
                ep_finale = ep_iniziale
                if ep_finale > anime.ep:
                    my_print(f"L'episodio {ep_iniziale} di {anime.name} non è ancora stato rilasciato!", color='rosso')
                    if len(log) == 1:
                        safeExit()
                    else:
                        sleep(1)
                        continue
            
            if downl:
                path = f"{downloadPath()}/{anime.name}"
                for ep in range(ep_iniziale, ep_finale+1):
                    scaricaEpisodio(ep, path)

                my_print("Tutti i video scaricati correttamente!\nLi puoi trovare nella cartella", color="verde", end=" ")
                if nome_os == "Android":
                    my_print("Movies/Anime", color="verde")
                else:
                    my_print("Video/Anime", color="verde")
                    
                    #chiedi all'utente se aprire ora i video scaricati
                    if my_input("Aprire ora il player con gli episodi scaricati? (S/n)", lambda i: i.lower()) in ['s', '']:
                        openVideos(ep_iniziale, ep_finale, ratingAnilist, preferitoAnilist, user_id)
                safeExit()

            ris_valida = True
            while True:
                if ris_valida:
                    openVideos(ep_iniziale,ep_finale, ratingAnilist, preferitoAnilist, user_id)
                else:
                    my_print("Seleziona una risposta valida", color="rosso")
                    ris_valida = True

                prossimo = True
                antecedente = True
                seleziona = True

                # menù che si visualizza dopo aver finito la riproduzione
                if ep_finale != anime.ep:
                    my_print("(p) prossimo", color="azzurro")
                else:
                    prossimo = False
                my_print("(r) riguarda", color="blu")
                if ep_finale != anime.ep_ini:
                    my_print("(a) antecedente", color="azzurro")
                else:
                    antecedente = False
                if anime.ep != 1:
                    my_print("(s) seleziona", color="verde")
                else:
                    seleziona = False
                my_print("(i) indietro", color='magenta')
                my_print("(e) esci", color="rosso")
                my_print(">", color="magenta", end=" ")
                scelta_menu = input().lower()
                if (scelta_menu == 'p' or scelta_menu == '') and prossimo:
                    ep_iniziale = ep_finale + 1
                    ep_finale = ep_iniziale
                    continue
                elif scelta_menu == 'r':
                    continue            
                elif scelta_menu == 'a' and antecedente:
                    ep_iniziale = ep_finale - 1
                    ep_finale = ep_iniziale
                    continue
                elif scelta_menu == 's' and seleziona:
                    ep_iniziale, ep_finale = scegliEpisodi()
                elif scelta_menu == 'i':
                    break
                elif scelta_menu == 'e':
                    safeExit()
                else:
                    my_print("", end="", cls=True)
                    ris_valida = False

        except KeyboardInterrupt:
            safeExit()

#args
downl = False
lista = False
offline = False
cronologia = False
info = False
privato = False
versione = "1.7fC"
log = []
player_path = ""
syncplay_path = ""
openPlayer = None

anime = Anime("", "")

if __name__ == "__main__":
    main()