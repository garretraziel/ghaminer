# DIP

## Z čeho budu brát data

- nejspíš hlavně GitHub API, knihovna [githubpy](https://github.com/michaelliao/githubpy)
- pro získání vzorku repozitářů ze kterých budu dolovat asi githubarchive, nicméně k ničemu víc asi nebude

## Jak budu brát data pro dolování

- napíšu crawler, který bude zjišťovat statistiky k repozitářům - střední doma čekání na opravu, medián, atp., spíš než jenom raw data
- crawler bude při clawrování ignorovat budoucí data a zjistí statistiky ke starším datům, následně se podívá i na události do budoucnosti a podle toho klasifikuje "byl aktivní"/"nebyl aktivní"
- aktivita by chtěla vyjádřit číslem asi, to by nakonec šlo tak, že bych vzal nejaktivnější v každé kategorii (commity, komentáře, pullrequesty...) a těm dal číslo "100", ostatním rovnoměrně od 0
- výsledkem bude obří soubor, který bude obsahovat zadaný počet repozitářů a v každém řádku nějaké sumární informace o aktivitě projektu
- následně můžu použít scikit-learn a už něco doopravdy začít učit
- jak nad tím přemýšlím, pro "je/není aktivní" můžu použít údaj `updated_at` - pokud je `updated_at` blízko dneška, je aktivní, pro začátek. po poradě s Bartíkem pak můžu i vzít dobu dlouho před `updated_at` a považovat ho v té době za aktivní. možná bych pak mohl předpovídat, jak dlouho ještě aktivní bude?

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
    - jednotka je commitů/den
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