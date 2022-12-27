import os
from bs4 import BeautifulSoup
import requests
import re
import mimetypes
import mpv
import time
from pySmartDL import SmartDL
from pathlib import Path
import hpcomt
import argparse


class Anime:
    name = ""
    ep = 0


def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')


def my_print(text: str, format=1, color="bianco", bg_color="nero", cls=False, end="\n"):
    COLORS = {'nero': 0,'rosso': 1,'verde': 2,'giallo': 3,'blu': 4,'magenta': 5,'azzurro': 6,'bianco': 7}
    if cls:
        os.system('cls' if os.name == 'nt' else 'clear')

    print(
        f"\033[{format};3{COLORS[color]};4{COLORS[bg_color]}m{text}\033[1;37;40m", end=end)


def listaUscite(selected: str) -> tuple[list[str], list[str]]:
    """scraping per le ultime uscite di anime se AW"""

    url_ricerca = "https://www.animeworld.tv"
    contenuto_html = requests.get(url_ricerca).text
    bs = BeautifulSoup(contenuto_html, "lxml")

    risultati_ricerca = []
    nomi_anime = []
    data_name = "all"

    if selected == "s":
        data_name = "sub"
    elif selected == 'd':
        data_name = "dub"

    div = bs.find("div", {"data-name": data_name})
    for div in div.find_all(class_='inner'):
        temp = ""
        risultati_ricerca.append("https://www.animeworld.tv" + div.a.get('href'))
        for a in div.find_all(class_='name'):
            temp = a.text
        for div in div.find_all(class_='ep'):
            temp += " [" + div.text + "]"
            nomi_anime.append(temp)

    return risultati_ricerca, nomi_anime


def RicercaAnime() -> tuple[list[str], list[str]]:
    """dato in input un nome di un anime inserito dall'utente,\n
    restituisce un lista con gli url degli anime
    relativi alla ricerca"""

    while True:
        my_print("Cerca un anime\n>", color="magenta", cls=True, end=" ")
        scelta = input()
        # esco se metto exit
        if (scelta == "exit"):
            exit()

        rimpiazza = scelta.replace(" ", "+")
        # cerco l'anime su animeworld
        url_ricerca = "https://www.animeworld.tv/search?keyword=" + rimpiazza

        my_print("Ricerco...", color="giallo")

        # prendo i link degli anime relativi alla ricerca
        contenuto_html = requests.get(url_ricerca).text
        bs = BeautifulSoup(contenuto_html, "lxml")

        risultati_ricerca = []
        nomi_anime = []

        div = bs.find(class_='film-list')
        for div in div.find_all(class_='inner'):
            risultati_ricerca.append("https://www.animeworld.tv" + div.a.get('href'))
            for a in div.find_all(class_='name'):
                nomi_anime.append(a.text)
        if (len(risultati_ricerca) != 0):
            return risultati_ricerca, nomi_anime
        else:
            my_print("La ricerca non ha prodotto risultati", color="rosso")
            time.sleep(1)


def UrlEpisodi(url: str) -> list[str]:
    """prende in input l'url dell'anime scelto dall'utente\n
    restituisce: gli url di tutti gli episodi"""

    # prendo l'html dalla pagina web di AW
    html_content = requests.get(url).text
    soup = BeautifulSoup(html_content, "lxml")
    url_episodi = []
    # cerco gli url di tutti gli episodi
    for div in soup.find_all(class_='server active'):
        for li in div.find_all(class_="episode"):
            temp = "https://www.animeworld.tv" + (li.a.get('href'))
            url_episodi.append(temp)
    return url_episodi


def TrovaUrl(string: str) -> list[str]:
    """trova qualsisi url in una stringa"""

    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]


def trovaUrlServer(url_ep: str) -> str:
    # creo un obj BS con la pagina dell'ep
    html = requests.get(url_ep).text
    sp = BeautifulSoup(html, "lxml")

    # variabile temp per capire in che posizione è l'url tra tutti gli url della pagina
    j = 0
    # ciclo for con il numoro totale degli url
    for url in TrovaUrl(str(sp)):
        # se l'url è un video e si trova in posizione 1 allora è quello del server
        if (mimetypes.MimeTypes().guess_type(url)[0] == 'video/mp4'):
            if (j == 1):
                return url
            j += 1


def scegliEpisodi(url_episodi: list[str]) -> tuple[int, int]:
    """fa scegliere gli ep da guardare all'utente"""
    
    my_print(a.name, cls=True)
    #se contiene solo 1 ep sarà riprodotto automaticamente
    if a.ep == 1:
        return 1, 1

    if lista:
        return a.ep, a.ep

    # faccio decire all'utente il range di ep
    while True:
        if (nome_os == "Android"):
            my_print("Attenzione! Su Android non è ancora possibile specificare un range per lo streaming", color="giallo")
        my_print(f"Specifica un episodio, o per un range usa: ep_iniziale-ep_finale (Episodi: 1-{str(a.ep)})\n>", color="magenta", end=" ")
        n_episodi = input()
        # controllo se l'utente ha inserito un range o un episodio unico (premere invio di default selezione automaticamente tutti gli episodi)
        if "-" not in n_episodi:
            if n_episodi == '':
                ep_iniziale = 1
                ep_finale = a.ep
                break
            else:
                ep_iniziale = int(n_episodi)
                ep_finale = int(n_episodi)
                if (ep_iniziale > a.ep or ep_iniziale < 1):
                    my_print("La ricerca non ha prodotto risultati", color="rosso")
                else:
                    break
        else:
            flag = 0
            temp1 = ""
            temp2 = ""
            for i in range(0, len(n_episodi)):
                if (flag == 0 and n_episodi[i] != '-'):
                    temp1 += n_episodi[i]
                if (n_episodi[i] == '-'):
                    flag = 1
                    continue
                if (flag == 1):
                    temp2 += n_episodi[i]

            ep_iniziale = int(temp1)
            ep_finale = int(temp2)
            if (ep_iniziale > ep_finale or ep_finale > a.ep or ep_iniziale < 1):
                my_print("La ricerca non ha prodotto risultati", color="rosso")
            else:
                break

    return ep_iniziale, ep_finale




def downloadPath():
    if (nome_os == "Android"):
        path = f"storage/downloads/{a.name}"
    else:
        path = f"{Path.home()}/Videos/Anime/{a.name}"
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def scaricaEpisodio(url_ep: str, path: str):
    """utilizza la libreria PySmartDL
    per scaricare l'ep e lo salva in una cartella.
    se l'ep è già presente nella cartella non lo riscarica"""

    gia_scaricato = 0
    my_print("Preparo il download...", color="giallo")
    nome_video = url_ep.split('/')[-1]

    # se l'episodio non è ancora stato scaricato lo scarico, altrimenti skippo
    my_print(f"Episodio: {nome_video}", color="blu")
    if not os.path.exists(str(path) + "/" + nome_video):
        SDL = SmartDL(url_ep, path)
        SDL.start()
    else:
        my_print("Episodio già scaricato, skippo...", color="giallo")
        gia_scaricato += 1


def open_Syncplay(url_ep: str):
    """crea un file dove inserisce i link
    degli episodi e avvia syncplay"""

    os.system(f"syncplay  {url_ep} -a syncplay.pl:8999 --language it &>/dev/null")


def OpenPlayer(url_server: str):
    """prende in input il link
    del video e apre il player per riprodurre il video"""

    if syncpl:
        open_Syncplay(url_server)
    elif (nome_os == "Android"):
        # apro il player utilizzando bash e riproduco un video
        # os.system("am start --user 0 -a android.intent.action.VIEW -d \"" +
        # url_server+"\" -n org.videolan.vlc/org.videolan.vlc.gui.video.VideoPlayerActivity -e \""+a.name+"ep "+str(a.ep)+"\" \"$trackma_title\" > /dev/null 2>&1 &")

        os.system("am start --user 0 -a android.intent.action.VIEW -d \"" +
                  url_server+"\" -n is.xyz.mpv/.MPVActivity > /dev/null 2>&1 &")
    else:
        player = mpv.MPV(input_default_bindings=True,
                         input_vo_keyboard=True, osc=True)

        # avvio il player
        player.fullscreen = True
        player.playlist_pos = 0
        player._set_property("keep-open", True)
        player.play(url_server)
        player.wait_for_shutdown()
        player.terminate()


def openDownlodedVideos(path_episodi: list[str]):
    for path_ep in path_episodi:
        nome_video = path_ep.split('/')[-1]
        my_print(f"Riproduco {nome_video}...", color="giallo", cls=True)
        OpenPlayer(path_ep)



def chiediSeAprireDownload(path_video: list[str]):
    while True:
        my_print("Aprire ora il player con gli episodi scaricati? (S/n)\n>", color="magenta", end=" ")
        match input().lower():
            case 's'|"": 
                openDownlodedVideos(path_video)
                break
            case 'n': break
            case  _: my_print("Seleziona una risposta valida", color="rosso")


def openVideos(url_episodi: list[str]):
    for url_ep in url_episodi:
        url_server = trovaUrlServer(url_ep)
        nome_video = url_server.split('/')[-1]
        my_print(f"Riproduco {nome_video}...", color="giallo", cls=True)
        OpenPlayer(url_server)


def main():
    global syncpl
    global download
    global lista

    # args
    parser = argparse.ArgumentParser("aw-cli", description="Guarda anime dal terminale e molto altro!")
    if nome_os != "Android":
        parser.add_argument('-s', '--syncplay', action='store_true', dest='syncpl', help='usa syncplay per guardare un anime insieme ai tuoi amici')
    parser.add_argument('-d', '--download', action='store_true', dest='download', help='scarica gli episodi che preferisci')
    parser.add_argument('-l', '--lista', nargs='?', choices=['a', 's', 'd'], dest='lista', help='lista degli ultimi anime usciti su AnimeWorld. a = all, s = sub, d = dub')
    args = parser.parse_args()

    if nome_os != "Android":
        if args.syncpl:
            syncpl = True
    if args.download:
        download = True
    elif args.lista:
        lista = True

    try:
        if lista:
            risultati_ricerca, nomi_anime = listaUscite(args.lista)
        else:
            risultati_ricerca, nomi_anime = RicercaAnime()
        while True:
            clearScreen()
            # stampo i nomi degli anime
            for i, nome in reversed(list(enumerate(nomi_anime))):
                my_print(f"{i + 1} ", color="verde", end=" ")
                my_print(nome)

            
            while True:
                my_print("Scegli un anime\n>", color="magenta", end=" ")
                s = int(input())-1
                # controllo che il numero inserito sia giusto
                if s in range(len(nomi_anime)):
                    break
                my_print("Seleziona una risposta valida", color="rosso")

            url = risultati_ricerca[s]
            url_episodi = UrlEpisodi(url)
            a.ep = len(url_episodi)

            # se l'anime non ha episodi non può essere selezionato
            if a.ep == 0:
                my_print("Eh, volevi! L'anime non ha episodi", color="rosso")
                time.sleep(1)
            else:
                break

        a.name = nomi_anime[s]
        # trovo il link del primo url server
        # creo un obj BS con la pagina dell'ep
        html = requests.get(url_episodi[0]).text
        sp = BeautifulSoup(html, "lxml")

        # variabile temp per capire in che posizione è l'url tra tutti gli url della pagina
        j = 0
        for url in TrovaUrl(str(sp)):
            # se l'url è un video e si trova in posizione 1 allora è quello del server
            if (mimetypes.MimeTypes().guess_type(url)[0] == 'video/mp4'):
                if (j == 1):
                    # aggiungo alla varibile sempre e solo l'url server del primo episodio
                    a.url = url
                    break
                j += 1

        ep_iniziale, ep_finale = scegliEpisodi(url_episodi)

        # se syncplay è stato scelto allora non chiedo
        # di fare il download ed esco dalla funzione
        if not syncpl and download:
            path_video = []
            path = downloadPath()
            for i in range(ep_iniziale - 1, ep_finale):
                url_ep = trovaUrlServer(url_episodi[i])
                nome_video = url_ep.split('/')[-1]
                scaricaEpisodio(url_ep, path)
                path_video.append(f"{path}/{nome_video}")

            my_print("Tutti i video scaricati correttamente!\nLi puoi trovare nella cartella", color="verde", end=" ")
            if nome_os == "Android":
                my_print("Downloads", color="verde")
            else:
                my_print("Video/Anime", color="verde")
                chiediSeAprireDownload(path_video)
            exit()

        ris_valida = True
        while True:
            if ris_valida:
                openVideos(url_episodi[ep_iniziale-1:ep_finale])
            else:
                my_print("Seleziona una risposta valida", color="rosso")
                ris_valida = True
            # menù che si visualizza dopo aver finito la riproduzione
            my_print("(p) prossimo", color="azzurro")
            my_print("(r) riguarda", color="blu")
            my_print("(a) antecedente", color="azzurro")
            my_print("(s) seleziona", color="verde")
            my_print("(e) esci", color="rosso")
            my_print(">", color="magenta", end=" ")
            scelta_menu = input().lower()
            if scelta_menu == 'p' and ep_iniziale < a.ep:
                ep_iniziale = ep_finale + 1
                ep_finale = ep_iniziale
                continue
            elif scelta_menu == 'r':
                continue
            elif scelta_menu == 'a' and ep_iniziale > 1:
                ep_iniziale = ep_finale - 1
                ep_finale = ep_iniziale
                continue
            elif scelta_menu == 's':
                ep_iniziale, ep_finale = scegliEpisodi(url_episodi)
            elif scelta_menu == 'e' or scelta_menu == '':
                exit()
            else:
                clearScreen()
                ris_valida = False

    except KeyboardInterrupt:
        exit()


# controllo il tipo del dispositivo
nome_os = hpcomt.Name()
#args
syncpl = False
download = False
lista = False
# classe
a = Anime()

if __name__ == "__main__":
    main()
