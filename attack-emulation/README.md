# Emulazione delle tecniche

I test girano solo su `win-01` (gruppo `lab`), con uno snapshot prima di ogni test e nessun payload nel repo. Uso Atomic Red Team direttamente sulla macchina, senza C2: la fase con C2 non l'ho eseguita, perché il lab non è ancora isolato dalla rete di casa ([architecture.md](../docs/architecture.md)).

| # | Tecnica ATT&CK | Test | Telemetria attesa (Sysmon) | Esito |
|---|---|---|---|---|
| 1 | T1059.001 PowerShell | T1059.001-17, -15, -10 | EID 1 | -17: 92057 (liv. 12); -15: 92071 (liv. 12); -10: 92041 (liv. 10); falso positivo 92213 (liv. 15) |
| 2 | T1053.005 Scheduled Task | T1053.005-2, -4, -6 | EID 1, 11 | nessun alert sulla creazione dell'attività, solo rumore da cmd e PowerShell |
| 3 | T1547.001 Run Keys | T1547.001-1, -2 | EID 13 | 92302 (liv. 6) e 92041 (liv. 10, falso positivo Base64) |
| 4 | T1136.001 Account locale | T1136.001-4, -5 | Security 4720, EID 1 | 92040 (liv. 12, solo test 4) e 60109 (liv. 8, entrambi) |
| 5 | T1070.001 Cancellazione log | manuale: `wevtutil cl Application` | System 104, EID 1 | solo 63104 (liv. 5); il processo non viene segnalato, da cui le regole 100013 e 100014 |

Il dettaglio di ogni prova, con i comandi e le schermate, è in [docs/procedure.md](../docs/procedure.md). Le regole e la loro verifica sono in [detections/README.md](../detections/README.md).

Collegati: [README](../README.md), [detections/README.md](../detections/README.md), [docs/procedure.md](../docs/procedure.md).
