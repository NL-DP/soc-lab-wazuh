# Rilevazioni

Le regole personalizzate sono cinque e stanno in [local_rules.xml](local_rules.xml). Tre tecniche su cinque erano già coperte dalle regole di default. Per le altre due ho scritto quattro regole, e la quinta (100010) serve a ridurre un falso positivo, non a coprire una lacuna. Ogni regola ha almeno un controllo negativo.

| Tecnica | Test | Alert di default | Regola mia | Falsi positivi osservati | Verifica |
|---|---|---|---|---|---|
| T1059.001 | 17, 15, 10 | 92057 (liv. 12), 92071 (liv. 12), 92041 (liv. 10) | nessuna | 92213 (liv. 15) a ogni avvio di PowerShell | non serve |
| tuning di 92213 | - | 92213 su `__PSScriptPolicyTest_*.ps1` | 100010 (liv. 3) | dopo la regola nessun nuovo 92213 di questo tipo: 3 avvii di PowerShell danno 3 alert 100010, 13 a fine giornata | dal vivo; controllo negativo: un `.ps1` con altro nome in `%TEMP%` crea ancora 92213 (liv. 15) |
| T1053.005 | 2, 4, 6 | nessuno sulla creazione dell'attività (solo rumore generico: 92004, 92052, 92032, 92027) | 100011 (liv. 8), 100012 (liv. 10) | nessuno in pochi minuti di osservazione, ma software legittimo crea attività: da misurare su più giorni | dal vivo sui tre test; le pulizie non generano alert; controlli negativi: un file in una cartella `Tasks` fuori da `System32` e `schtasks /query` non fanno scattare le regole |
| T1547.001 | 1, 2 | 92302 (liv. 6), 92041 (liv. 10), 92052 (liv. 4) | nessuna | 92041 è un'euristica Base64 che scatta su un percorso normale | non serve |
| T1136.001 | 4, 5 | 92040 (liv. 12, solo test 4), 60109 (liv. 8, entrambi) | nessuna | nessuno osservato | non serve; richiede l'audit "Gestione account utente" |
| T1070.001 | manuale | 63104 (liv. 5, solo l'effetto); nessun alert sul processo | 100013 (liv. 10), 100014 (liv. 10) | nessuno osservato | dal vivo; controlli negativi: `wevtutil gli Application` e `wevtutil epl Application` non fanno scattare le regole; `Clear-EventLog` non è coperto |

I falsi positivi li ho osservati solo per pochi minuti e vanno misurati su più giorni.

## Controlli negativi
Un controllo negativo è un evento simile ma innocuo, che non deve far scattare la regola. Per ognuno ho verificato prima che Sysmon registrasse davvero l'evento, altrimenti l'assenza dell'alert non proverebbe niente.

| Regola | Evento simile ma innocuo | Esito |
|---|---|---|
| 100010 | `.ps1` con un altro nome in `%TEMP%` | 92213 a livello 15, nessun 100010 |
| 100011 | `.ps1` creato in `%TEMP%\Tasks\` (cartella con lo stesso nome, fuori da `System32`) | 92213 per il `.ps1`, nessun 100011 |
| 100012 | `schtasks /query` (stesso eseguibile, solo lettura) | nessun 100012 |
| 100013 | `wevtutil epl Application` (esporta il log senza cancellarlo) | nessun 63104, nessun 100013 |
| 100014 | `wevtutil gli Application` e `wevtutil epl Application` | nessun 100014 |

I tre nuovi controlli (100011, 100012, 100013) li ho eseguiti il 22 ottobre 2026 su `win-01`, ciascuno una volta, e ho letto gli alert dei minuti successivi:
```powershell
schtasks /query | Select-Object -First 5
New-Item -ItemType Directory "$env:TEMP\Tasks" -Force | Out-Null
Set-Content "$env:TEMP\Tasks\prova-controllo.ps1" "# controllo negativo"
wevtutil epl Application "$env:TEMP\app-export.evtx" /ow:true
```
Il primo tentativo di `wevtutil epl` è fallito (file di destinazione già esistente) e non conta: l'ho rifatto con `/ow:true` e ho controllato che il file fosse stato scritto. Per la 100011 ho verificato in locale, con `Get-WinEvent`, che Sysmon avesse registrato la creazione del file (evento 11). Nella stessa finestra ci sono stati alert di sistema senza legame con i comandi (92217, 92307, 61138), che ho escluso dall'elenco.

Limiti dei controlli: uno per regola, eseguito una volta. Non ho provato varianti di evasione, per esempio altre forme dei parametri di `schtasks`, che la regola 100012 potrebbe non riconoscere.

Un alert reale per ogni regola, ripulito, è in [samples/](samples/README.md). Tre regole tradotte in Sigma sono in [sigma/](sigma/README.md), e la copertura per tecnica è in [coverage](../coverage/README.md).

## Come provo una regola
1. Faccio un backup di `/var/ossec/etc/rules/local_rules.xml` sul manager e aggiungo il blocco in coda.
2. Controllo la sintassi con `sudo /var/ossec/bin/wazuh-analysisd -t`: deve terminare con codice 0.
3. Riavvio con `sudo systemctl restart wazuh-manager`.
4. Riproduco l'evento su `win-01` e cerco l'alert nella dashboard o in `alerts.json` (con `grep -a`).
5. Provo un evento simile ma innocuo: deve dare ancora la regola originale, non la mia.

Collegati: [README](../README.md), [docs/procedure.md](../docs/procedure.md), [attack-emulation/README.md](../attack-emulation/README.md), [writeups/README.md](../writeups/README.md).
