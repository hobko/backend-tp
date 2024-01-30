**V priecinku /storage/csv/ su vzorove CSV subory na ktorych je to mozne otestovat** 
# SKONTROLOVAT .env a precitat si komentaru k tomu
# Lokalne spustenie (nie DOCKER)
## Ako spustit Angular prvy krat 
- **Navštívte oficiálnu stránku [Node.js](https://nodejs.org/) a stiahnite si node**
- ```npm install -g @angular/cli```
- ```npm install```
- ```ng serve```
## Ako spustit flask api prvy krat 
- **Skontrolovat ci je nainstalovany Python(idealne 3.9.x)**
- **Pre instalaciu balickov treba napisat**  
  - ```pip install -r requirements.txt```
  - Po zbehnuti treba napisat do terminalu prikaz
  - ```uvicorn main:app --reload```

    
## Ako spustit graphhopper prvy krat 

- **Potreba JDK ADOPTIUM >= 17 [Klikni tu pre presmerovanie na adoptium](https://adoptium.net/)**
- **Nasledne treba do konzoly napisat tieto prikazy**
  - ```Invoke-WebRequest -Uri https://repo1.maven.org/maven2/com/graphhopper/graphhopper-web/8.0/graphhopper-web-8.0.jar -OutFile graphhopper-web-8.0.jar```
  - ```Invoke-WebRequest -Uri https://raw.githubusercontent.com/graphhopper/graphhopper/8.x/config-example.yml -OutFile config-example.yml```
  - ```Invoke-WebRequest -Uri http://download.geofabrik.de/europe/slovakia-latest.osm.pbf -OutFile slovakia-latest.osm.pbf```
  - **Po dokonceni tychto krokov pre spustenie napisat**
  - ```java -D"dw.graphhopper.datareader.file=slovakia-latest.osm.pbf" -jar graphhopper-web-8.0.jar server config-example.yml```

# DOCKER spustenie
- **Vytvorit si folder do ktoreho sa naklonuju nižšie zmienené repozitáre(momentalny pocet 3)**
- **Prepnut sa do backend projektu (cez cd kvoli lokalizacii súboru)**
  - **do cmd treba napísať nasledovný príkaz**
    - ```docker-compose up``` **One command to rule them all!**
  - **Mometalne by sa to malo rozbehnut FE a BE naskocia skoro hned no s graphopperom treba pockat treba si kontrolovat konzolu alebo kde to spustate kym neuvidite ```INFO  org.eclipse.jetty.server.Server - Started```**
  
# PORTY na ktorých aplikácie bežia
- **Backend - teda (fast api) bezi aj v dockeri aj pri lokalnom spusteni na adrese ```http://127.0.0.1:8000```**
- **Map-matching - teda (Graphhopper) bezi na dvoch portoch. Port 8989 je usera posielame nan reqeusty. Port 8990 je na admin správu, momentálne ho nevyužívame ale od budúcna ho máme ready**
  - **Docker**
    - ```http://graphhopper:8989```
      - **sem príma requesty od fast-api**
    - ```http://graphhopper:8990``` 
      - **admin rozhranie**
  - **Local run**
    - ```http://localhost:8989```
    - ```http://localhost:8990```
- **Frontend - teda (Angular)**
  - **Docker**
    - ```http://localhost:8080```
  - **Local run**
    - ```http://localhost:4200```
# Github aplikácie
### **Momentalne pouzivame len 3 a to map-matching, backend, frontend**
- [graphhopper](https://github.com/hobko/graphoppertp)
- [backend](https://github.com/hobko/backend-tp)
- [frontend](https://github.com/hobko/TP-1)