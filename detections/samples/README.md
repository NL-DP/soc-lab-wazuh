# Alert di esempio

Qui c'è un alert reale per ognuna delle cinque regole mie, più i due alert di default (92040 e 60109) del test T1136.001-4. Servono a vedere quali campi leggono le regole. Sono i primi alert di `win-01` per ciascuna regola nel file `alerts.json` del manager del 18 ottobre 2026.

Li ho ripuliti prima di pubblicarli: il nome del manager è `wazuh-mgr`, il computer è `win-01`, l'utente è `user` e i SID sono rimossi. Ho tolto anche `full_log`, che ripete tutto il contenuto di `data`, il campo `message` con il testo su più righe, i GUID e gli hash. Il resto è com'è uscito da Wazuh. L'indirizzo `10.0.2.15` è quello della rete NAT predefinita di VirtualBox.

| File | Regola | Evento che la fa scattare | Campi che la regola legge |
|---|---|---|---|
| [100010.json](100010.json) | 100010 | Sysmon 11, file creato da PowerShell | `image`, `targetFilename` |
| [100011.json](100011.json) | 100011 | Sysmon 11, file creato in `System32\Tasks` | `targetFilename` |
| [100012.json](100012.json) | 100012 | Sysmon 1, `schtasks.exe /Create` | `image`, `commandLine` |
| [100013.json](100013.json) | 100013 | System 104, log cancellato | eredita da 63104 |
| [100014.json](100014.json) | 100014 | Sysmon 1, `wevtutil.exe cl` | `image`, `commandLine` |
| [92040.json](92040.json) | 92040 (default) | Sysmon 1, `net1.exe user /add` | - |
| [60109.json](60109.json) | 60109 (default) | Security 4720, account creato | - |

## Cosa si vede negli alert

I percorsi hanno i backslash raddoppiati nel valore stesso dei campi (`C:\\Windows\\System32\\...`), non solo nella codifica JSON. Per questo le espressioni delle regole usano `\\+` e non `\\`.

La 100011 non scatta per `schtasks.exe` ma per `svchost.exe` che gira come `NT AUTHORITY\SYSTEM`: è il servizio Utilità di pianificazione che scrive il file di definizione. È il motivo per cui la regola funziona con tutti e tre i metodi di creazione e non solo con il comando.

La 100013 e la 100014 vengono dalla stessa operazione. Il `clientProcessId` (8644) nell'alert 100013 è il `processId` di `wevtutil.exe` nell'alert 100014, e i due alert sono distanti circa un secondo.

L'ora dell'evento (`systemTime`, in UTC) e l'ora dell'alert (`timestamp`, locale, +0200) non coincidono:

| Alert | Ritardo dell'alert rispetto all'evento |
|---|---|
| 100013 | -0,4 s (l'alert è datato prima dell'evento) |
| 100014 | +0,6 s |
| 92040, 60109 | +7,6 s e +7,8 s |
| 100010 | +9,1 s |
| 100011, 100012 | +44,7 s |

Gli alert dello stesso test hanno ritardi quasi uguali, e uno è negativo: nel ritardo c'è anche la differenza tra l'orologio della VM e quello del manager, quindi non è un tempo di consegna puro. Per questo attribuisco gli alert ai test per ordine e non per orario.

Collegati: [detections/README.md](../README.md), [local_rules.xml](../local_rules.xml), [docs/procedure.md](../../docs/procedure.md).
