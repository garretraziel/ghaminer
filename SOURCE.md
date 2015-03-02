# Popis zdroje dat

- vstupním souborem jsou projekty, přičemž jeden projekt je popsán jedním repozitářem systému git
- projekt má nějakou dobu vzniku (založení stránky na githubu nebo první commit, záleží co přišlo dřív) a dostatečně staré projekty (víc jak rok bez zaslání změny) také dobu ukončení (doba poslední změny)
- uživatelé do repozitáře zasílají změny (commity). změna kódu je určena časem, kdy byla tato změna vykonána
- jiní uživatelé mohou hlásit chyby v projektu, přičemž tyto chyby mohou být opraveny nějakou změnou, nebo zavřeny z jiného důvodu
- další uživatelé mohou zasílat takzvané pull requesty, změny, které nepocházejí od autorů
- mohu zjistit frekvenci zasílání změn - počet zaslání za časovou jednotku - pro naše potřeby počet commitů za jeden týden
- frekvence zasílání změn kódu určují aktivitu projektu
- míru budoucího vývoje můžeme určit jako podíl budoucí a aktuální frekvence. pokud je toto číslo větší jak 1, projekt bude vyvíjen a aktivita bude stoupat. pokud bude menší jak 1, aktivita projektu bude upadat. pokud se blíží 0, projekt nebude dále vyvíjen
- de fakto můžu experimentovat s časovou jednotkou pro frekvenci. asi nikoho nezajímá, jakej bude vývoj projektu příští týden, takže se zřejmě bude porovnávat frekvence uplynulého a budoucího měsíce
