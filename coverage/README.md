# Copertura

Una vista sola di quello che ho emulato e di come lo rileva Wazuh. Il dettaglio di ogni prova è in [detections/README.md](../detections/README.md); qui c'è il riassunto per tecnica.

| Tecnica | Rilevata di default | Regola mia | Esito |
|---|---|---|---|
| T1059.001 PowerShell | sì (92057, 92071, 92041) | 100010 riduce il falso positivo 92213 | coperta |
| T1053.005 Scheduled Task | no | 100011, 100012 | lacuna chiusa |
| T1547.001 Run Keys | sì (92302) | nessuna | coperta |
| T1136.001 Account locale | sì (92040, 60109) | nessuna | coperta; il test 5 (PowerShell) solo dall'audit di Security, quindi dipende dall'audit "Gestione account utente" |
| T1070.001 Cancellazione log | solo l'effetto, a livello 5 (63104) | 100013, 100014 | lacuna chiusa, tranne `Clear-EventLog` |

## Layer di ATT&CK Navigator
[attack-layer.json](attack-layer.json) è un layer per [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/). Per aprirlo: Open Existing Layer, Upload from local, e scelgo il file. Azzurro vuol dire rilevata dalle regole di default, verde vuol dire coperta da una regola mia. Il commento di ogni tecnica dice quali regole la rilevano. Gli ID delle tecniche sono quelli che Wazuh riporta negli alert; li ho riscontrati sul sito di MITRE ATT&CK il 22 ottobre 2026 (T1070.001 solo sulla versione 16 del sito, perché la pagina attuale non era raggiungibile). Le tecniche non colorate sono quelle che non ho provato.

Non ho ancora esportato un'immagine del layer: si vede aprendo il file nel Navigator.

## Sigma
Tre delle mie regole le ho tradotte in Sigma, in [detections/sigma](../detections/sigma/README.md), per vedere cosa si perde nel passaggio.

Collegati: [README](../README.md), [STRUTTURA.md](../STRUTTURA.md), [detections/README.md](../detections/README.md).
