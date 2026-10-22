# L'89% degli alert 92213 non era il file che pensavo

## Sintomo
Dopo il primo test su `win-01` la dashboard si riempie di alert 92213 ("Executable file dropped in folder commonly used by malware", livello 15, T1105), anche per comandi innocui. Prima di intervenire erano 100; a fine giornata sono 102 (`evidence/07-alert-fatigue-92213.png`). A livello 15 questi alert coprono quelli veri: chi guarda la dashboard smette di leggerli.

## Diagnosi
Ho preso l'alert grezzo di un caso. È un evento Sysmon 11 (file creato) del processo `powershell.exe`, sul file `%TEMP%\__PSScriptPolicyTest_<casuale>.ps1`. Questo file lo crea PowerShell da solo a ogni avvio, per verificare la modalità del linguaggio: non è un eseguibile scaricato. La regola 92213 sta in `/var/ossec/ruleset/rules/0830-sysmon_id_11.xml` ed è figlia della 61613 (Sysmon 11, livello 0).

Ho ipotizzato che tutti i 100 alert fossero di quel tipo. Prima di scrivere la regola ho contato l'origine di ognuno sul file `alerts.json` del giorno:

| Origine | Alert |
|---|---|
| `__PSScriptPolicyTest_*.ps1` creato da `powershell.exe` | 11 |
| script `TestHarnesses\Txxxx_*.ps1` del modulo AtomicTestHarnesses (dipendenza del test T1059.001-15) | circa 89 |

L'ipotesi era sbagliata per quasi nove alert su dieci. Se avessi scritto la regola sulla sola convinzione iniziale, o l'avrei fatta troppo larga o avrei lasciato fuori quasi tutto il rumore senza capire perché.

## Soluzione
Ho scritto una regola figlia della 92213 (ID 100010 in `detections/local_rules.xml`) che porta a livello 3 solo il caso che ho verificato essere benigno: processo `powershell.exe` e nome file che corrisponde esattamente al modello `__PSScriptPolicyTest_*.ps1`. Ho scelto una combinazione stretta di processo e nome perché abbassare tutta la cartella `%TEMP%` nasconderebbe proprio il comportamento che la 92213 deve segnalare.

Per validarla ho seguito questi passi:
1. Backup di `local_rules.xml`, controllo con `wazuh-analysisd -t` (codice di uscita 0), riavvio del manager.
2. Tre avvii di PowerShell: producono tre alert 100010 a livello 3 e nessun nuovo 92213 di questo tipo. A fine giornata i 100010 sono 13 (`evidence/08-rule-100010-after.png`).
3. Controllo negativo: un file `prova-controllo.ps1` creato in `%TEMP%` genera ancora un 92213 a livello 15.

## Lezione
Conto l'origine degli alert prima di scrivere la regola, perché la prima ipotesi può essere sbagliata anche se sembra ovvia. Abbasso il livello solo per una combinazione stretta e verificata. I circa 89 alert del modulo di test non li sopprimo: sono rumore del test e li lascio visibili di proposito. Se in una misura su più giorni risultano troppo invasivi, decido allora se vale la pena una regola sul percorso.

Collegati: [writeups/README.md](README.md), [detections/README.md](../detections/README.md), [docs/procedure.md](../docs/procedure.md).
