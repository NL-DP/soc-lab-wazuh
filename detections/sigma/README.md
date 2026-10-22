# Regole Sigma

Tre delle mie regole Wazuh tradotte in [Sigma](https://sigmahq.io/), il formato che i SIEM diversi leggono. Le ho scritte per vedere cosa si perde nel passaggio, non per sostituire le regole Wazuh.

| File | Regola Wazuh | Cosa rileva |
|---|---|---|
| [wevtutil-clear-log.yml](wevtutil-clear-log.yml) | 100014 | `wevtutil.exe` con `cl` o `clear-log` |
| [schtasks-create.yml](schtasks-create.yml) | 100012 | `schtasks.exe` con `/create` |
| [scheduled-task-definition-file.yml](scheduled-task-definition-file.yml) | 100011 | file creato in `System32\Tasks` |

Le ho convertite in Splunk con `sigma convert -t splunk -p splunk_windows` per controllare che la sintassi sia valida e che le espressioni regolari vengano portate così come sono. Non le ho provate su dati veri.

## Cosa si perde
La 100010 e la 100013 non hanno una traduzione. La 100010 abbassa il livello di un'altra regola per un falso positivo, e la 100013 alza il livello della 63104: sono modifiche a regole di Wazuh, e Sigma descrive cosa rilevare, non come cambiare una regola altrui.

Le altre tre perdono tre cose. Wazuh lega la regola al gruppo di eventi Sysmon (`sysmon_event1`), mentre Sigma dice solo "creazione di processo", valida anche per l'evento 4688 di Security. I livelli numerici di Wazuh (da 0 a 15) diventano le cinque classi di Sigma e la corrispondenza (10 a `high`, 8 a `medium`) l'ho scelta io. I backslash raddoppiati nei campi di Wazuh (`\\+` nelle espressioni, vedi [samples](../samples/README.md)) spariscono: se ne occupa il backend, e un backend per Wazuh dovrebbe gestirli.

Collegati: [detections/README.md](../README.md), [coverage/README.md](../../coverage/README.md).
