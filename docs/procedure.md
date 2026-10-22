# Procedura

Questa è la procedura con cui ho costruito il lab e fatto i test, nell'ordine in cui l'ho eseguita. Stato dei passi: rete e VM (fatto), Wazuh e agent (fatto), Sysmon (fatto), lettura degli eventi (fatto), baseline (eseguita in forma ridotta), emulazione (fatto), regole (fatto).

## 1. Rete e VM

| Macchina | Tipo | Risorse | Note |
|---|---|---|---|
| wazuh-mgr | VM Linux Mint 22.2 su Proxmox | 4 vCPU, 8 GB RAM, 63 GB disco | Wazuh 4.14.8 (manager, indexer, dashboard) |
| win-01 | VM Windows 11 Home (build 26300) su VirtualBox | 8 vCPU, 8 GB RAM | rete NAT, agent 4.14.8, Sysmon 15.22, Atomic Red Team |

A fine tecniche ho fatto uno snapshot VirtualBox di `win-01` in stato pulito (agent, Sysmon e Atomic Red Team installati, nessuna traccia dei test). Lo ripristino prima di ogni nuova sessione di test. La rete di `win-01` è la NAT di VirtualBox: vedi [architecture.md](architecture.md).

## 2. Wazuh e agent

### 2.1 Gruppi di agent
Gli agent stanno in due gruppi: `lab`, con le macchine su cui lancio i test, e `default`, con i dispositivi della rete di casa, che ricevono questo gruppo di base. Sul manager creo solo il gruppo del laboratorio:
```bash
sudo /var/ossec/bin/agent_groups -a -g lab -q
```

### 2.2 Agent Windows (win-01)
1. Controllo la rete verso il manager da PowerShell come amministratore. La porta 1515 serve per la registrazione dell'agent e la 1514 per l'invio degli eventi; entrambe devono rispondere `TcpTestSucceeded : True`.
   ```powershell
   Test-NetConnection <MANAGER_IP> -Port 1515
   Test-NetConnection <MANAGER_IP> -Port 1514
   ```
2. Controllo sul manager che il gruppo esista. I nomi dei gruppi distinguono maiuscole e minuscole:
   ```bash
   sudo /var/ossec/bin/agent_groups -l
   ```
3. Dalla dashboard vado su Agents, Deploy new agent, scelgo Windows, indirizzo del manager, nome `win-01`, gruppo `lab`. Eseguo il comando generato in PowerShell come amministratore e avvio il servizio:
   ```powershell
   NET START WazuhSvc
   ```
4. Se il servizio non parte o l'agent non compare sul manager, leggo il log:
   ```powershell
   Get-Content "C:\Program Files (x86)\ossec-agent\ossec.log" -Tail 25
   ```
   Se nome o gruppo salvati sono sbagliati, reinstallare non basta e registro di nuovo l'agent a mano. `agent-auth` deve stampare `Valid key received`. Il caso reale è nel [write-up 01](../writeups/01-gruppo-agent-case-sensitive.md).
   ```powershell
   NET STOP WazuhSvc
   & "C:\Program Files (x86)\ossec-agent\agent-auth.exe" -m <MANAGER_IP> -A win-01 -G lab
   NET START WazuhSvc
   ```
5. Verifico sul manager. Mi aspetto `win-01` con stato `Active` (schermata: `evidence/01-agents-active.png`).
   ```bash
   sudo /var/ossec/bin/agent_control -l
   ```

La versione dell'agent deve essere uguale o inferiore a quella del manager.

## 3. Sysmon

### 3.1 Installazione su win-01
Uso Sysmon 15.22 (Sysinternals, Microsoft) con la configurazione pubblica di SwiftOnSecurity (`sysmonconfig-export.xml`, che non includo nel repo: fonte https://github.com/SwiftOnSecurity/sysmon-config). Da PowerShell come amministratore:
```powershell
cd $env:USERPROFILE\Downloads
Invoke-WebRequest https://download.sysinternals.com/files/Sysmon.zip -OutFile Sysmon.zip
Expand-Archive Sysmon.zip -DestinationPath Sysmon -Force
Invoke-WebRequest https://raw.githubusercontent.com/SwiftOnSecurity/sysmon-config/master/sysmonconfig-export.xml -OutFile sysmonconfig.xml
.\Sysmon\Sysmon64.exe -accepteula -i sysmonconfig.xml
Get-Service Sysmon64
```
Mi aspetto `Sysmon64 installed`, `SysmonDrv installed` e il servizio `Running` (schermata: `evidence/02-sysmon-running.png`).

### 3.2 Lettura degli eventi in Wazuh
Questo passo è verificato: gli eventi Sysmon arrivano al manager e compaiono come alert in dashboard. La lettura del canale di Sysmon si configura una volta sola sul manager, nel file condiviso del gruppo `lab`, così vale per tutti gli agent del gruppo senza toccare le singole macchine.

1. Sul manager creo o modifico `/var/ossec/etc/shared/lab/agent.conf`. Una copia pulita è in [config/lab-agent.conf](../config/lab-agent.conf).
   ```xml
   <agent_config os="Windows">
     <localfile>
       <location>Microsoft-Windows-Sysmon/Operational</location>
       <log_format>eventchannel</log_format>
     </localfile>
   </agent_config>
   ```
2. Verifico la sintassi:
   ```bash
   sudo /var/ossec/bin/verify-agent-conf
   ```
3. Aspetto la sincronizzazione, qualche minuto. L'agent riceve la configurazione dal manager senza riavvio manuale.
4. In Discover filtro su `agent.name: win-01` e sul provider `Microsoft-Windows-Sysmon`: devono comparire eventi Sysmon (Event ID 1, 3, 11, 13). Un esempio di alert derivato da un evento Sysmon è in `evidence/04-T1059.001-default.png`.

La dashboard mostra solo gli eventi che hanno generato un alert, cioè con regola di livello 3 o superiore. Per controllare che il flusso funzioni anche per gli eventi senza alert, attivo temporaneamente `<logall_json>yes</logall_json>` nella sezione `<global>` di `/var/ossec/etc/ossec.conf` del manager, riavvio il manager e cerco in `/var/ossec/logs/archives/archives.json`:
```bash
sudo grep -c 'Microsoft-Windows-Sysmon' /var/ossec/logs/archives/archives.json
```
Poi rimetto il valore a `no`, perché l'archivio cresce in fretta e occupa disco.

## 4. Baseline
L'ho eseguita in forma ridotta: 3 ore e 9 minuti invece di 24 ore. È il periodo di `win-01` dall'iscrizione dell'agent (14:56) al primo test (18:05 circa), senza tecniche d'attacco. Ha tre limiti. Dura circa 3 ore. Sysmon è attivo solo dalle 17:31, quindi gli eventi Sysmon coprono meno di 40 minuti. I due agent di produzione non li ho usati, perché non hanno Sysmon configurato. Una baseline su 24 ore o più, con Sysmon già attivo, è il passo che manca.

In quella finestra `win-01` ha prodotto 738 alert (orari locali), estratti dal file `alerts.json` del giorno con uno script che legge un alert JSON per riga; la versione ripulita dello script è [scripts/count-alerts.py](../scripts/README.md). Un primo conteggio con `grep` ne scartava una parte, perché alcune descrizioni contengono virgolette.

| Gruppo | Alert | Regole | Orari | Valutazione |
|---|---|---|---|---|
| Scansione SCA (benchmark CIS) | 497 (67%) | 19007 (352, liv. 7), 19008 (117), 19009 (21), 19005 (3, liv. 9), 19014/19015 | 15:01 (prima scansione), 17:32 (seconda, dopo il riavvio dell'agent) | evento unico a ogni scansione, non è comportamento anomalo; è il rumore principale |
| Sistema Windows | 175 | 60608 (119), 60716 (25), 61104 (21), 60702 (4), 60642 (3), 61138 (2), 61102 (1) | raffica 17:18:42-17:18:51; 61104 dalle 14:57; 61138 alle 15:10 | attività del sistema operativo (la 60716 cita `wuauserv`, Windows Update); causa della raffica delle 17:18 non analizzata |
| PowerShell/Sysmon | 56 | 92205 (20, liv. 9), 92021 (16), 92066 (16), 92031 (4) | 17:32:00-17:32:21 | raffica di 20 secondi in coincidenza con l'installazione di Sysmon e il riavvio dell'agent (17:32:11-12); non ho eseguito nessuna tecnica; la causa esatta non l'ho verificata |
| Agent Wazuh | 8 | 503 e 506 (3 + 3), 501, 657 | 14:56-17:32 | avvii, arresti e iscrizione dell'agent |
| Falso positivo noto | 1 | 92058 (liv. 12): Application Compatibility Database launched, T1546.011 | 17:41:56 | `sdbinst.exe -m -bg` è avviato dal servizio Windows Program Compatibility Assistant (PcaSvc) |
| Altro | 1 | regola 11 (liv. 4, senza descrizione) | 17:32:31 | non classificato |

Ne ricavo due cose per il seguito. Il rumore di fondo ad alto livello è quasi tutto SCA (livelli 3-9) più brevi raffiche, quindi nelle finestre dei test gli alert da confrontare con la baseline sono quelli di livello 8 o superiore su Sysmon e Security. E le raffiche delle 17:18 e delle 17:32 mostrano che installazioni e riavvii dell'agent producono decine di alert di PowerShell che con i test non c'entrano.

Schermata: `evidence/00-baseline.png` (dashboard, `win-01`, intervallo assoluto 14:56-18:05, senza filtro di livello).

## 5. Emulazione

### 5.1 Preparazione di win-01
I test li eseguo solo su `win-01` (gruppo `lab`). Prima di ogni sessione controllo con `hostname` che il nome sia quello della VM di laboratorio, poi:

1. Faccio lo snapshot della VM.
2. Escludo la cartella dei test dai controlli di Defender, perché gli script vengono segnalati come malevoli:
   ```powershell
   Add-MpPreference -ExclusionPath "C:\AtomicRedTeam"
   ```
3. Installo Invoke-AtomicRedTeam con lo script ufficiale di Red Canary. Se è già installato lo script lo segnala e non modifica nulla. Non uso `-Force`, perché cancella l'installazione esistente.
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   IEX (IWR 'https://raw.githubusercontent.com/redcanaryco/invoke-atomicredteam/master/install-atomicredteam.ps1' -UseBasicParsing)
   Install-AtomicRedTeam -getAtomics
   ```
4. Verifico con l'elenco dei test di una tecnica, che non esegue nulla. L'`Import-Module` va ripetuto a ogni nuova sessione di PowerShell.
   ```powershell
   Import-Module "C:\AtomicRedTeam\invoke-atomicredteam\Invoke-AtomicRedTeam.psd1" -Force
   Invoke-AtomicTest T1059.001 -ShowDetailsBrief
   ```
5. Controllo in sola lettura i residui di test precedenti. Trovo solo gli account di default e l'utente locale, nessuna attività pianificata e nessuna voce di avvio automatico.
   ```powershell
   Get-LocalUser | Select-Object Name, Enabled
   Get-ScheduledTask | Where-Object {$_.TaskPath -eq '\'} | Select-Object TaskName, State
   Get-ItemProperty HKCU:\Software\Microsoft\Windows\CurrentVersion\Run
   ```

### 5.2 Scelta dei test (T1059.001, PowerShell)
Ho usato `T1059.001-17` (PowerShell Command Execution), `T1059.001-15` (-EncodedCommand parameter variations) e `T1059.001-10` (PowerShell Fileless Script Execution). Ho escluso Mimikatz (1, 4), BloodHound (2, 3, 21, 22), PowerUp (19) e i cmdlet dichiaratamente malevoli (18): Defender li blocca e non servono a una prima dimostrazione di rilevazione.

Prima di ogni esecuzione leggo cosa farà il test, e dopo pulisco:
```powershell
Invoke-AtomicTest T1059.001 -TestNumbers 17 -ShowDetails
Invoke-AtomicTest T1059.001 -TestNumbers 17 -Cleanup
```

### 5.3 Esecuzione dei test
Per ogni test registro la data, la catena di processi, la telemetria Sysmon osservata, gli alert di default di Wazuh e una schermata. Le cinque tecniche sono tutte completate.

#### T1059.001-17 (PowerShell Command Execution)
Il comando decodificato (base64 UTF-16LE) è `& (gcm ('ie{0}' -f 'x')) ("Wr"+"it"+"e-H"+"ost 'Hello, from PowerShell!'")`: stampa un messaggio, non scrive file e non apre connessioni.

| Campo | Valore |
|---|---|
| Data | 2026-10-18, esecuzione alle 18:08 (CEST) |
| Catena di processi | `powershell.exe` (sessione amministratore) → `cmd.exe /c powershell.exe -e <base64>` → `powershell.exe` |
| Telemetria Sysmon | EID 1 (`cmd.exe` con riga di comando `powershell.exe -e <base64>`), EID 11 (file creato da `powershell.exe`) |
| Alert di default | 92057, livello 12: PowerShell avviato da PowerShell con comando codificato in base64, T1059.001 (vero positivo) |
| Alert di default | 92213, livello 15: eseguibile creato in una cartella usata dai malware, T1105 (falso positivo, vedi sotto) |
| Schermata | `evidence/04-T1059.001-default.png` |

Il falso positivo 92213 è scattato per il file `%TEMP%\__PSScriptPolicyTest_<casuale>.ps1`, che `powershell.exe` crea da solo all'avvio per verificare la modalità del linguaggio. Non è un eseguibile scaricato, ma la regola di default lo classifica comunque al livello più alto (15) e lo associa a T1105 (Ingress Tool Transfer). L'ho trattato con la regola 100010 (sezione 6).

#### T1059.001-15 (-EncodedCommand parameter variations)
Il test usa il modulo `AtomicTestHarnesses` di Red Canary, che non è incluso in Atomic Red Team e si installa dal PowerShell Gallery con `Invoke-AtomicTest T1059.001 -TestNumbers 15 -GetPrereqs`. La prima esecuzione è fallita perché il modulo non c'era (`Out-ATHPowerShellCommandLineParameter` non riconosciuto) e non ha generato telemetria; il risultato qui sotto riguarda la seconda, a modulo installato. Il comando codificato, decodificato, è `Write-Host <GUID casuale>`: stampa un identificatore e basta.

| Campo | Valore |
|---|---|
| Test | variante `-E` |
| Data | 2026-10-18, esecuzione alle 18:21 (CEST) |
| Catena di processi | `WmiPrvSE.exe -secured -Embedding` → `powershell.exe -NoProfile -E <base64>` |
| Telemetria Sysmon | EID 1 (processo con `-E` e padre WMI), 6 × EID 1 `csc.exe` con padre `powershell.exe` (compilazione C# del modulo), EID 11 `__PSScriptPolicyTest_*.ps1` |
| Alert di default | 92071, livello 12: PowerShell creato da WMI con comando in base64, T1047 e T1059.001 (vero positivo) |
| Alert di default | 92213, livello 15, falso positivo ripetuto (stesso file di prova di PowerShell) |

Per i test 17 e 15 le regole di default rilevano entrambe le catene (92057 e 92071), quindi qui non serve una regola di rilevazione mia. Il valore sta nel ridurre i falsi positivi: la 92213 ha prodotto 97 alert di livello 15 in circa mezz'ora dall'avvio dei test. Il totale della giornata, contato più tardi, è 100 (vedi sotto).

#### T1059.001-10 (PowerShell Fileless Script Execution)
Il test salva nel registro un payload codificato in base64 e lo esegue da lì. Il payload, decodificato, è `Set-Content -path "$env:SystemRoot/Temp/art-marker.txt" -value "Hello from the Atomic Red Team"`: scrive un file marcatore e non fa altro. I residui da togliere con `-Cleanup` sono la chiave `HKCU\Software\Classes\AtomicRedTeam` e il file `C:\Windows\Temp\art-marker.txt`.

| Campo | Valore |
|---|---|
| Data | 2026-10-18, esecuzione alle 18:29 (CEST) |
| Telemetria Sysmon | EID 1 `powershell.exe` con commento sul payload, EID 1 `reg.exe add HKCU\Software\Classes\AtomicRedTeam /v ART /t REG_SZ /d <base64> /f` |
| Alert di default | 92041, livello 10: valore aggiunto a una chiave di registro con pattern simile a base64 (vero positivo) |
| Alert di default | 92027, livello 4: PowerShell avviato da PowerShell (generico) |
| Alert di default | 92213, livello 15, falso positivo |

#### Falsi positivi della 92213 (livello 15)
Sul file degli alert del 2026-10-18 ho contato 100 alert 92213 in totale:

| Origine | Alert | Valutazione |
|---|---|---|
| `__PSScriptPolicyTest_*.ps1` in `%TEMP%`, creato da `powershell.exe` a ogni avvio | 11 | falso positivo ricorrente: ci ho scritto la regola 100010 |
| script `TestHarnesses\Txxxx_*.ps1` in `%TEMP%` del modulo AtomicTestHarnesses | circa 89 | effetto dell'installazione della dipendenza del test 15: rumore atteso del test, non lo sopprimo |

I numeri dipendono da quando li ho contati: 97 dopo circa mezz'ora dall'avvio dei test, 100 sul file del giorno (è su questo che si calcola 11 + 89), 102 nella schermata 07. La differenza tra 100 e 102 non l'ho verificata.

Schermate: `evidence/07-alert-fatigue-92213.png` (102 alert 92213 a fine giornata) e `evidence/08-rule-100010-after.png` (13 alert 100010 a livello 3 dopo la regola). Il ragionamento è nel [write-up 03](../writeups/03-falso-positivo-92213-psscriptpolicytest.md).

Per T1059.001 quindi i tre test (17, 15, 10) sono rilevati dalle regole di default (92057, 92071, 92041) e il mio lavoro riguarda i falsi positivi.

#### T1053.005 (Scheduled Task): test 2, 4 e 6
Ho scelto tre test che creano l'attività con tre metodi diversi: `schtasks.exe` (2), cmdlet PowerShell (4), WMI (6). Ho escluso il 3 (richiede un computer remoto), il 5 (richiede Office), il 13 e il 14 (riproducono malware reale) e il 10, 11 e 12 (modificano chiavi di registro di sistema o dirottano il gestore dei file `.msc`). I test 1, 7, 8 e 9 non li ho eseguiti.

| Test | Cosa crea | Esecuzione (CEST) |
|---|---|---|
| 2 | `schtasks /Create /SC ONCE /TN spawn /TR C:\windows\system32\cmd.exe /ST 20:10` | 18:52 |
| 4 | attività `AtomicTask` (`calc.exe` al logon, gruppo Administrators, privilegi massimi) con `Register-ScheduledTask` | 18:53 |
| 6 | attività `T1053_005_WMI` (`notepad.exe` al login) registrata con la classe WMI `PS_ScheduledTask` (`RegisterByXml`) | 18:54-18:55 |

Le tre attività le ho rimosse con `-Cleanup` e ho controllato con `Get-ScheduledTask` che non restasse nulla.

Telemetria Sysmon osservata (controllo locale con `Get-WinEvent`):

| Test | Eventi |
|---|---|
| 2 | EID 1 `cmd.exe /c SCHTASKS /Create ...`, EID 1 `schtasks.exe /Create ...`, EID 11 `C:\Windows\System32\Tasks\spawn` |
| 4 | EID 1 `powershell.exe` con `New-ScheduledTaskAction`, EID 11 `C:\Windows\System32\Tasks\AtomicTask` |
| 6 | EID 1 `powershell.exe` con `ReadAllText(...T1053_005_WMI.xml)`, EID 11 `C:\Windows\System32\Tasks\T1053_005_WMI` |

Non ci sono eventi di registro (EID 12 e 13) sulle chiavi `TaskCache`, perché la configurazione Sysmon che uso non li registra. Nei test 4 e 6 la riga di comando con i cmdlet è visibile solo perché Atomic Red Team avvia un `powershell.exe` figlio; un attaccante già dentro una sessione aperta non produrrebbe quel processo. Il segnale comune ai tre metodi è la creazione del file di definizione in `C:\Windows\System32\Tasks\`. Nell'alert della regola 100011 il file risulta scritto da `svchost.exe` come `NT AUTHORITY\SYSTEM`, cioè dal servizio Utilità di pianificazione, e non dal processo che ha lanciato il test ([alert di esempio](../detections/samples/100011.json)).

Gli alert di default (sei esecuzioni, test e pulizia) sono solo regole generiche sul processo che avvia `cmd.exe` o `powershell.exe` (92004 e 92052 a livello 4, 92032 a livello 3, 92027 a livello 4), più la 100010 sui `PSScriptPolicyTest`. Nessun alert menziona un'attività pianificata: per T1053.005 le regole di default non rilevano i tre test, ed è la lacuna su cui ho scritto le regole 100011 e 100012 (sezione 6). Schermata: `evidence/09-T1053.005-default-none.png` (finestra 18:52-18:57).

Dopo averle aggiunte ho rieseguito i tre test con pulizia. Il test 2 genera la 100012 (livello 10) e la 100011 (livello 8); i test 4 e 6 generano la 100011. Le pulizie non producono alert e non restano attività (`Get-ScheduledTask` vuoto). Schermata: `evidence/10-T1053.005-custom-rule.png` (alert 100011). Il racconto è nel [write-up 04](../writeups/04-lacuna-t1053-005-scheduled-task.md).

Per verificare la telemetria in locale, indipendentemente da Wazuh, uso il registro eventi di Windows:
```powershell
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Sysmon/Operational'; Id=1} -MaxEvents 15 |
  Where-Object { $_.Message -match 'powershell' } |
  ForEach-Object { $_.TimeCreated; ($_.Message -split "\r?\n" | Select-String '^CommandLine') }
```

#### T1547.001 (Run Keys): test 1 e 2
Ho scelto il test 1 (valore `Atomic Red Team` in `HKCU\...\Run`) e il 2 (valore `1` in `HKLM\...\RunOnceEx\0001\Depend`). Entrambi scrivono con `reg.exe` un percorso inesistente (`C:\Path\AtomicRedTeam.exe` e `.dll`), quindi anche al login non eseguirebbero nulla. Pulisco con `-Cleanup` (`REG DELETE`). Prima del test la chiave `RunOnceEx` non esisteva; la pulizia ufficiale elimina il valore ma non le chiavi create.

Gli alert sono uguali per i due test (test e pulizia a circa 15 secondi l'uno dall'altra):

| Fase | Regola | Livello | Significato |
|---|---|---|---|
| scrittura del valore | 92052 | 4 | `cmd.exe` avviato da processo anomalo |
| scrittura del valore | 92041 | 10 | "Value added to registry key has Base64-like pattern" |
| scrittura del valore | 92302 | 6 | "Registry entry to be executed on next logon was modified using command line application reg.exe" |
| pulizia | 92052 | 4 | `reg delete` |

La tecnica è rilevata dalle regole di default (92302), sia per `Run` sia per `RunOnceEx`, quindi non ho scritto una regola. La 92041 è un'euristica che scatta su un percorso normale, non Base64: un falso positivo di classificazione a livello 10 che non ho trattato. Schermata: `evidence/11-T1547.001-default.png`.

#### T1136.001 (Account locale): test 4 e 5
Ho scelto il test 4 (`net user /add T1136.001_CMD`, da `cmd`) e il 5 (`New-LocalUser -Name T1136.001_PowerShell -NoPassword`). Ho eliminato i due utenti con `-Cleanup` e `Get-LocalUser` non li mostra più.

| Test | Alert (processo) | Alert (Security) |
|---|---|---|
| 4 | 92052 (liv. 4), 92036 (liv. 3), 92040 (liv. 12, "net1.exe executed a user creation command") | 60109 (liv. 8, account creato, EID 4720), 60110, 60160, 60170 |
| 5 | nessuna regola sul processo (solo 92027 e 100010, rumore noto) | 60109 (liv. 8), 60110, 60160 |
| pulizie | 92039 (test 4) | 60111 (liv. 8, account disabilitato o eliminato) |

Entrambi i test sono rilevati dalle regole di default. Il test 4 lo vedono sia il processo (92040) sia l'evento Security; il test 5 solo l'evento Security 4720, perché il cmdlet non avvia un eseguibile dedicato. La rilevazione dipende quindi dall'audit "Gestione account utente", che è attivo (l'evento 4720 è arrivato a Wazuh). Schermata: `evidence/12-T1136.001-default.png` (92040). Gli alert reali del test 4 sono in [detections/samples](../detections/samples/README.md). La ricostruzione completa, dagli alert, è nel [report di incidente](incident-report-01.md).

#### T1070.001 (Cancellazione log): esecuzione manuale
La cartella `T1070.001` non esiste nella copia locale di Atomic Red Team (`Test-Path` = False), quindi ho eseguito il test a mano. È equivalente al test standard ma sul solo log Application: `wevtutil.exe cl Application`, da PowerShell.

| Fase | Telemetria / alert |
|---|---|
| Sysmon EID 1 | `wevtutil.exe cl Application`, padre `powershell.exe` (registrato, ma senza alert) |
| System 104 ("File di registro Application cancellato") | Wazuh 63104, livello 5, MITRE T1070 (generico) |
| Security 1102 | assente (non ho cancellato il log Security) |

L'effetto è rilevato di default, ma a livello 5, mentre il processo non produce alcun alert: la lacuna è sul livello e sul processo, da cui le regole 100013 e 100014 (sezione 6). Le ho validate rieseguendo `wevtutil.exe cl Application` (alert 100013 e 100014 entro 2 secondi l'uno dall'altro) e con i controlli negativi `wevtutil.exe gli Application` e `wevtutil.exe epl Application`, che non generano alert. `Clear-EventLog` di PowerShell resta coperto solo dalla 100013, non da una regola sul processo: servirebbe abilitare lo Script Block Logging (evento 4104), che non ho provato.

Schermate: `evidence/13-T1070.001-default.png` (63104, livello 5) e `evidence/14-T1070.001-custom-rules.png` (100013, con il nome utente coperto).

Una nota sull'orario: l'ora dell'evento (campo `systemTime` dell'alert, in UTC) e l'ora dell'alert non coincidono, e la differenza nei sette alert che ho misurato va da -0,4 a +45 secondi ([detections/samples](../detections/samples/README.md)). Dentro c'è anche lo scarto tra l'orologio della VM e quello del manager. Per questo le ore dei comandi su `win-01` e quelle degli alert non coincidono, e attribuisco gli alert ai test per ordine e non per ora.

## 6. Regole personalizzate
La fase è completata. Dettagli e misure sono in [detections/README.md](../detections/README.md); le regole sono in [detections/local_rules.xml](../detections/local_rules.xml).

| ID | Livello | Scopo |
|---|---|---|
| 100010 | 3 | abbassa il falso positivo 92213 sui file `__PSScriptPolicyTest_*.ps1` creati da `powershell.exe` |
| 100011 | 8 | T1053.005: file di definizione creato in `C:\Windows\System32\Tasks\` (qualunque metodo) |
| 100012 | 10 | T1053.005: `schtasks.exe` con `/create` |
| 100013 | 10 | T1070.001: alza a 10 la 63104 (log di Windows cancellato) |
| 100014 | 10 | T1070.001: `wevtutil.exe` con `cl` o `clear-log` |

Il metodo di validazione, per ogni regola:
1. Backup di `local_rules.xml`, aggiunta del blocco, controllo con `sudo /var/ossec/bin/wazuh-analysisd -t` (codice di uscita 0) e riavvio del manager.
2. Riproduzione dell'evento su `win-01` e verifica dell'alert in `alerts.json` (con `grep -a`).
3. Controllo negativo: un evento simile ma diverso non deve far scattare la regola. Per la 100010, un `.ps1` con altro nome in `%TEMP%` dà ancora 92213 a livello 15. Per la 100011, un `.ps1` in `%TEMP%\Tasks\` non fa scattare la regola. Per la 100012, `schtasks /query`. Per la 100013, `wevtutil epl Application` (esporta senza cancellare). Per la 100014, `wevtutil gli Application`. I comandi e gli esiti sono in [detections/README.md](../detections/README.md#controlli-negativi).

Nei campi di Windows le barre rovesciate sono raddoppiate, anche nella descrizione interpolata `$(win.eventdata.targetFilename)`: per questo le espressioni usano `\\+`. Si vede negli [alert di esempio](../detections/samples/README.md).

Collegati: [docs/README.md](README.md), [README](../README.md), [detections/README.md](../detections/README.md), [attack-emulation/README.md](../attack-emulation/README.md).
