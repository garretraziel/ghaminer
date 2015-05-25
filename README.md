GitHub Activity Mining - stáhnutí datasetu
==========================================

Dolování budoucí aktivity projektů ze serveru GitHub - část pro stáhnutí datasetu ze serveru GitHub
pro machine learning.

Instalace
---------

Pro instalaci je vhodné použít program virtualenv.

1. (volitelně) vytvořte virtualenv pomocí:

        virtualenv ~/gham_virtualenv
        source ~/gham_virtualenv/bin/activate

2. Nainstalujte požadované knihovny:

        pip install -r requirements.txt

Použití
-------

Pro stahování je potřeba účet na serveru GitHub. Nastavte proměnné terminálu pomocí:

    export GH_USERNAME=username
    export GH_PASSWORD=password

kde `username` a `password` je jméno a heslo účtu na serveru GitHub.

Následně spusťte aplikaci pomocí:

    python ghaminer/ghaminer.py

Výsledný dataset, pojmenovaný `output.csv` je vytvořen v lokálním adresáři. Pro další možnosti
spuštění této aplikace použijte:

    python ghaminer/ghaminer.py -h
