# Write-up

Qui racconto i problemi che ho incontrato mentre costruivo il lab e come li ho diagnosticati. Le regole e i risultati dicono cosa ho fatto; i write-up dicono perché, comprese le ipotesi che ho dovuto correggere. Ognuno segue la stessa traccia: sintomo, diagnosi, soluzione, lezione.

I due sul lavoro di detection sono i più rappresentativi: il 03 e il 04. Gli altri due riguardano l'installazione e servono a chi vuole rifare il lab.

- [03 - L'89% degli alert 92213 non era il file che pensavo](03-falso-positivo-92213-psscriptpolicytest.md): una regola di livello 15 scattava a ogni avvio di PowerShell. Ho contato l'origine degli alert, scoperto che l'ipotesi era sbagliata e scritto la regola 100010 solo per il caso certo.
- [04 - Sysmon vedeva ogni attività pianificata, Wazuh non ne segnalava nessuna](04-lacuna-t1053-005-scheduled-task.md): la telemetria c'era ma nessuna regola la interpretava. Come sono nate le regole 100011 e 100012.
- [01 - Il manager rifiutava l'agent perché "Lab" non è "lab"](01-gruppo-agent-case-sensitive.md): il servizio non partiva e l'agent non compariva sul manager per una maiuscola nel nome del gruppo.
- [02 - Dashboard "not ready" dopo il riavvio: l'indexer va in timeout all'avvio](02-indexer-timeout-al-boot.md): l'indexer andava in timeout all'avvio della VM e la dashboard restava ferma. La prima soluzione (10 minuti) non bastava: al secondo riavvio ho misurato circa il 95% di I/O wait.

Collegati: [STRUTTURA.md](../STRUTTURA.md), [detections/README.md](../detections/README.md), [README](../README.md).
