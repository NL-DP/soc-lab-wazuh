# Il manager rifiutava l'agent perché "Lab" non è "lab"

## Sintomo
Sull'agent Windows `NET START Wazuh` fallisce con l'errore di sistema 1067 ("termine imprevisto del processo"). Dopo una seconda installazione il servizio parte, ma l'agent non compare sul manager.

## Diagnosi
Ho letto il log dell'agent (`ossec.log`) e la causa è in una riga sola:
```
wazuh-agent: ERROR: Invalid group: Lab. Unable to add agent (from manager)
```
Il gruppo creato sul manager si chiama `lab`, mentre nel comando di installazione avevo scritto `Lab`. In Wazuh i nomi dei gruppi distinguono maiuscole e minuscole, quindi il manager rifiutava la registrazione e l'agent restava in un ciclo di richieste senza ottenere una chiave.

Reinstallare con il gruppo corretto non è bastato: la seconda installazione, fatta sopra la prima, ha mantenuto la configurazione già salvata, cioè nome e gruppo del primo tentativo.

## Soluzione
Ho registrato l'agent a mano con i valori giusti, senza disinstallare:
```powershell
NET STOP WazuhSvc
& "C:\Program Files (x86)\ossec-agent\agent-auth.exe" -m <MANAGER_IP> -A win-01 -G lab
NET START WazuhSvc
```
Il comando risponde `Valid key received` e l'agent risulta `Active` sul manager.

## Lezione
Leggo `ossec.log` dell'agent prima di reinstallare: qui avrebbe evitato la seconda installazione inutile. Controllo con `agent_groups -l` il nome esatto dei gruppi sul manager. Per correggere nome o gruppo di un agent uso `agent-auth`, non una reinstallazione.

Collegati: [writeups/README.md](README.md), [docs/procedure.md](../docs/procedure.md), [docs/architecture.md](../docs/architecture.md).
