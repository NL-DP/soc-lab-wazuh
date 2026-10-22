# Architettura

## Componenti

| Nome      | Tipo                                                                                              | Ruolo                             | Gruppo Wazuh |
| --------- | ------------------------------------------------------------------------------------------------- | --------------------------------- | ------------ |
| wazuh-mgr | VM Linux Mint 22.2 su Proxmox (4 vCPU, 8 GB RAM, 63 GB disco)                                     | manager, indexer, dashboard       | -            |
| win-01    | VM Windows 11 Home (build 26300) su VirtualBox, host fisico separato (8 vCPU, 8 GB RAM), rete NAT | vittima, Sysmon                   | lab          |
| prod-01   | PC Windows 11                                                                                     | monitoraggio della rete domestica | default      |
| prod-02   | PC Windows 11                                                                                     | monitoraggio della rete domestica | default      |

## Lab e rete di casa sono separati per gruppo
Gli agent stanno in due gruppi Wazuh. `lab` contiene le macchine su cui lancio i test. `default` è il gruppo che ogni agent riceve di base e contiene i due PC di casa, che non attacco mai. Scrivo e provo le regole prima sul lab, e solo dopo guardo i falsi positivi sui PC di casa.

## Rete di `win-01`
`win-01` è una VM VirtualBox in modalità NAT, sulla rete 10.0.2.0/24 predefinita di VirtualBox. L'agent contatta il manager sulle porte 1514 e 1515 e la VM non è raggiungibile dall'esterno. I test che richiedono una connessione verso la VM devono quindi partire da lei, in uscita.

## Isolamento di rete: stato e piano
La NAT impedisce le connessioni in ingresso verso `win-01`, ma non limita quelle in uscita: oggi il lab può raggiungere la LAN domestica e Internet. Per questo non ho ancora fatto una fase con C2.

Il piano è una VLAN dedicata `cyber` su OPNsense:

- [ ] VLAN `cyber` creata
- [ ] Regola: dal lab al manager solo sulle porte 1514 e 1515
- [ ] Nessun accesso dal lab alla LAN domestica
- [ ] Nessun accesso dal lab a Internet, salvo finestre controllate
- [x] Snapshot VirtualBox di `win-01` a fine tecniche, in stato pulito (agent, Sysmon e Atomic Red Team installati)

Collegati: [docs/README.md](README.md), [README](../README.md), [docs/procedure.md](procedure.md).
