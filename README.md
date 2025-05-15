# bike-planner-mcp

## Overzicht
Deze applicatie is een modulaire reisplanner gebouwd met FastAPI, speciaal ontworpen voor het plannen van fietsroutes. De app maakt gebruik van een zogeheten MCP (Modular Command Processor) architectuur, waarmee verschillende tools (functies) in een logische volgorde kunnen worden aangeroepen op basis van gebruikersinvoer.

## Functionaliteit en Logica
De app biedt de volgende kernfunctionaliteiten:
- **Routeplanning:** Genereert een route-segment op basis van een startlocatie en gewenste afstand.
- **Weersvoorspelling:** Haalt een 3-daagse weersvoorspelling op voor een opgegeven locatie.
- **Slaapplek Suggestie:** Stelt een geschikte slaapplek voor aan het einde van de dag.
- **Activiteiten Zoeken:** Vindt activiteiten in de buurt van een locatie op basis van gebruikersvoorkeuren.

### Hoe werkt het?
1. **Gebruikersprompt:** De gebruiker geeft een verzoek (bijvoorbeeld: "Plan een fietstocht van Groningen naar Zwolle met natuuractiviteiten").
2. **Planningslogica:** De app vraagt een LLM (Large Language Model) om een plan te maken in de vorm van een lijst van tool-aanroepen, waarbij elke stap de benodigde argumenten bevat.
3. **Uitvoering:** De app voert de stappen uit, waarbij de resultaten van eerdere stappen als input kunnen dienen voor volgende stappen (middels placeholders zoals `<get_route_day.end>`).
4. **Resultaat:** De resultaten van alle stappen worden teruggegeven aan de gebruiker, inclusief de tussenresultaten.

## MCP Algemeen
MCP (Modular Command Processor) is een architectuur waarbij een centrale processor (de app) verschillende modulaire tools kan aanroepen op basis van een dynamisch gegenereerd plan. Dit maakt het mogelijk om complexe workflows flexibel en uitbreidbaar te maken, bijvoorbeeld voor reisplanning, data-analyse, of andere automatiseringstaken.

### Gebruik van MCP in deze app
- Tools worden gedefinieerd met naam, beschrijving en parameters.
- De LLM bepaalt op basis van de gebruikersvraag welke tools in welke volgorde worden aangeroepen.
- Resultaten van tools kunnen als input dienen voor volgende tools via placeholders.

## Meer leren over MCP
Wil je meer weten over MCP of deze app uitbreiden? Kijk dan op de [Smithery MCP documentatie](https://github.com/smithery-co/mcp) of neem contact op met de ontwikkelaars van dit project.

## Installatie en starten
1. Installeer de vereiste Python packages (zie requirements.txt).
2. Start de server met:
   ```bash
   uvicorn app:app --reload
   ```
3. Gebruik de `/run` endpoint om plannen te genereren en uit te voeren.
