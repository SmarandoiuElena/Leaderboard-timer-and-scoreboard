## Issues cu aplicatia de timer pentru AcadNet

### 1. Critice

    1.1. **Infrastructura**: Aplicatia nu are un backend propriu-zis. Simuleaza un fel de "baza de date" cu csv-uri dar asta introduce probleme de eficienta si fiabilitate, precum si probleme de sincronizare, totul fiind static.
    
    *Solutie propusa*: Separarea clara intre frontend si un backend minimal, care sa comunice si cu o baza de date. H2 si Sqlite sunt optiuni foarte simple si lightweight. 

### 2. Importante

    2.1. **Sincronizarea datelor**: Datele nu se updateaza automat si aplicatia trebuie restartata pentru a vedea orice schimbari. Se trage in principal din (1.1.).

    *Solutie propusa*: Echipele, steagurile, incercarile etc. sa fie fetched la runtime, din baza de date. Posibilitatea de a modifica DIN INTERFATA APLICATIEI datele: echipele, checkpoint-urile de la viteza, modificarea incercarilor etc.

    2.2. **Frontend-ul pentru elevi**: Ecranul de timer si cele de clasamente pe care le vad elevii arata profund vibecodate.

    *Solutie propusa*: Rescrierea styling-ului pentru timer si clasamente astfel incat sa respecte identitatea vizuala a AcadNet (sau macar sa arate putin facute de mana umana), fara elementele caracteristice frontend-ului scris de LLM-uri (gradients, culorile si tipografia, breadcrumbs si chip-uri unde nu au ce cauta etc.)

    2.3. **Codebase-ul**: Codul nu este modular si este foarte greu de urmarit. Totul este scris in main.py-ul de 400 de linii

    *Solutie propusa*: Modularizarea codului, impartirea in module de data access, websockets, endpoints, services etc.

### 3. Nitpicks

    3.1. **Containerizare**: Functionarea depinde complet de sistemul care hosteaza uvicorn. Daca cineva il opreste din greseala e pa aplicatia.

    *Solutie propusa*: Un setup minimal de docker + port forwarding ca sa fie mai determinist comportamentul aplicatiei

    3.2. **UI/UX pentru organizatori**: Unele elemente de UI/UX din panoul de arbitru sunt putin contra-intuitive. Nu este neaparat o problema daca arbitrul (sau arbitrii) au ocazia sa exploreze putin aplicatia inainte de probe.

    *Solutii propuse*: 

    * Inlocuirea ideii de "pauza" a timer-ului cu "final de cursa".
    * Ecran de confirmare pentru schimbarea probei din viteza in control (si invers).
    * Folosirea emojiurilor de steaguri in loc de imagini statice
    * ...
