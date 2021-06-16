import  extract.extractAdresse as extractAdresse
import  extract.extractText as extractText

def findAddress(metadata: dict, parser: str):
    
    pfad = next(iter(metadata))
    datei = next(iter(metadata[pfad]))
    inhalt = metadata[pfad][datei]['inhalt']
    
    # Pfad   
    adressen, adresse, adrName = extractAdresse.getAddress(pfad)  
    # Dateiname
    if not adressen:
        adressen, adresse, adrName = extractAdresse.getAddress(datei)
    # Inhalt
    if not adressen:
        if inhalt == '':
            inhalt = extractText.getTextContent(metadata, parser)

        adressen, adresse, adrName = extractAdresse.getAddress(inhalt) #inhalt = inhalt.split('§')[0]
    return adressen, adresse, adrName