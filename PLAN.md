# DIP

## Z čeho budu brát data

- nejspíš hlavně GitHub API, knihovna [githubpy](https://github.com/michaelliao/githubpy)
- pro získání vzorku repozitářů ze kterých budu dolovat asi githubarchive, nicméně k ničemu víc asi nebude

## Jak budu brát data pro dolování

- napíšu crawler, který bude zjišťovat statistiky k repozitářům - střední doma čekání na opravu, medián, atp., spíš než jenom raw data
- crawler bude při clawrování ignorovat budoucí data a zjistí statistiky ke starším datům, následně se podívá i na události do budoucnosti a podle toho klasifikuje, jak moc bude vyvíjen
- aktivita by chtěla vyjádřit číslem asi, to by nakonec šlo tak, že bych vzal nejaktivnější v každé kategorii (commity, komentáře, pullrequesty...) a těm dal číslo "100", ostatním rovnoměrně od 0
- výsledkem bude obří soubor, který bude obsahovat zadaný počet repozitářů a v každém řádku nějaké sumární informace o aktivitě projektu
- následně můžu použít scikit-learn a už něco doopravdy začít učit

## Co budu dolovat

1. id
2. jméno
3. jestli se jedná o fork
4. počet stargazerů
5. počet forků
6. počet sledujících
7. počet otevřených issues
8. počet subscribnutých
9. velikost
10. kdy bylo pushnuto
11. kdy bylo vytvořeno
12. kdy bylo updatováno
13. počet otevřených ticketů
14. počet uzavřených ticketů
15. poměr celkového početu ticketů ku uzavřeným
16. průměrná doba od nahlášení ticketu po jeho zavření (u zavřených ticketů)

## Co je to aktivní projekt

- aktivita bude podmíněná zasíláním kódu - cokoliv jiného - komentáře, labelování, vytváření wiki... nebude bráno jako aktivita projektu (tohle by chtělo nejdřív konzultovat)
- aktivní projekt je tedy takový, do kterého bude v budoucnu zaslán commit
- to znamená, že musím brát historii a "stav repozitáře ke dni X"
- problém: když mi zbývá jen jeden commit v budoucnu, označím projekt jako "aktivní", ale hodnoty budou skoro stejné, jako u mrtvého

### Řešení přes frekvenci commitů

- definuji frekvenci commitů (celkem jednoduše) jako: `f_comm(t) = C_comm(t)/(t - t_0)`
    - frekvence commitů v čase `t` je počet commitů zaslaných do `t` lomeno dobou od začátku projektu do času `t`
    - jednotka je commitů/týden
- aktivita v čase `t` je pak frekvence commitů v čase `t` lomeno celkovou frekvencí commitů (frekvence commitů v konečném čase `t_end`)

#### Výhody

- zohledňuje fakt, že do některých aktivních projektů zasílají lidi změny pravidelně, ale málo často
- počítá (rozumně) s budoucností, takže to není spočítatelné bez machine learningu

#### Nevýhody

- nutnost dobře vysvětlit, že když je projekt na vrcholu svých sil, tzn. v budoucnu do něj už lidi budou posílat míň a míň,
  je výsledek aktivity nejmenší (protože doteď je vysoká frekvence, pak už bude nízká frekvence commitů)
- nemám ponětí, jaký bude výsledek s corner casem, kde do konce projektu zbývá už jen jeden commit
- jak nad tím přemýšlím, nevím jestli je to správná definice. v bodě, kdy do projektu zasílají lidé nejvíce změn bude říkat,
  že projekt aktivní není (protože frekvence commitů se bude vždy už jenom snižovat), ale na konci života projektu bude říkat,
  že je aktivita slušná (když třeba poslední commit projektu pošlou dostatečně brzo, tudíž bude frekvence na konci vyšší,
  než aktuální frekvence)
  
#### Řešení

- šlo by:
    1) v podílu místo f_comm(t_end) počítat s f_comm(t_příští-commit)
    2) v podílu místo f_comm(t_end) počítat s nejvyšší frekvencí f_max
- asi použiji variantu 2) - stejně znám celou historii repozitáře, taky díky tomu získám číslo od 0 do 1

## Problémy

- nevím, jestli mám aktivitu počítat od prvního commitu, nebo od chvíle, kdy byl repozitář vytvořen
- u forků jsou commity ještě před vytvořením repozitáře - to zamává s aktivitou. počítat s nimi, nebo ne?
- u forků budu muset brát commity i z předchozího repozitáře, protože podle času created_at nepoznám nic. někdo může nejdřív dlouho psát a commitovat a až potom vytvořit repozitář
- asi bude problém u repozitářů, kam člověk během jednoho dne nahrál X commitů a tím to skončilo

## Výsledek

- musím si od teď dát pozor na pusu. měním pojmy, se kterými pracuji. aktivita od teď bude okamžitá, definovaná jako počet zaslání za poslední měsíc
- to co budu ve skutečnosti dolovat je "míra budoucího vývoje projektu", která je definována jako podíl aktivity příštího měsíce a aktuálního měsíce
    - to znamená, že pokud je větší než jedna, bude aktivita projektu růst, pokud bude jedna, bude stejná, pokud bude menší než jedna, bude aktivita klesat, pokud se bude blížit nule, projekt přestane být aktivní

# Konečné řešení
- aktivitu musím nahradit termínem "míra budoucího vývoje"
- mám tři různé definice aktivity - poměr dosavadní a budoucí frekvence změn, procento commitů co zbývá a budoucí frekvence (budoucího týdne, měsíce, půl roku, roku) - tady si budu moct pohrát s grafama
- budoucí míru vývoje nejlépe popisuje budoucí frekvence, přičemž v závislosti na dobu existence repozitáře to je příštý týden, půl rok, případně rok. bohužel, nejlepší odhady získám na procenta commitů, proto to bude taky to, co budu odhadovat
- zkouším nejrůznější metody - nejdřív Weka a vyhodnocování, z Weky jako nejlepší vypadl RandomForrest (korelační koeficient 0.65, RMSE 19 - dalo by se usuzovat na úspěšnost cca 80 %). Po experimentech ve scikit-learn (další spousta grafů) zatím nejlíp vypadá metoda GradientBoostingRegressor s RMSE 17.
- binning a následná klasifikace moc nefungují - zřejmě je to způsobeno tím, že funkce, co ohodnocuje správně vs. špatně klasifikovaný nebere v potaz jak velká vzdálenost od správné klasifikace byla
- možná není špatný nápad provést po regresi následné rozdělení do X (nejspíš tří) skupin - přesná hodnota uživatele stejně nezajimá a z části se tím potře chyba - zajimavé je, že i po binningu do tří skupin to háže stejnou hodnotu korelačního koeficientu (a RMSE je 0.44, nicméně to je trochu nicneříkající)

# Další poznatky
- napsat do DIP, že by pro výslednou aplikaci bylo vhodné, pokud by bylo potřeba škálovat, použít http://en.wikipedia.org/wiki/Time_series_database
