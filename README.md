# Praxis-Auftrag Tag 10: Monitoring-Umgebung mit Ansible & AWS Dynamic Inventory

## Übersicht

In diesem Praxisauftrag erweitern Sie die Infrastruktur aus **Tag 07** (SonarQube Server auf AWS EC2). Sie setzen deklarativ eine vollständige Container-Monitoring-Umgebung (**cAdvisor**, **Prometheus**, **Grafana**) auf der bestehenden VM mittels **Ansible** und dem **AWS EC2 Dynamic Inventory Plugin** auf.

---

## Sozialform & Ziel

- **Sozialform**: Einzel- oder Partnerarbeit
- **Ziel**:
  1. Anpassen der Terraform Security Group aus Tag 07 für Monitoring-Ports.
  2. Erstellen eines dynamischen AWS Inventorys mit `amazon.aws.aws_ec2`.
  3. Erstellen eines Ansible Playbooks, welches:
     - Automatisch die Terraform Security Group aktualisiert.
     - Docker & Git auf der EC2 VM installiert.
     - Das Repository `https://gitlab.com/ser-cal/m169-scripts.git` klont.
     - Die Monitoring-Services (`KN05_B`) per Docker Compose startet.

---

## Voraussetzungen

- Funktionierende AWS CLI mit Learner Lab Credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`).
- SSH-Schlüssel unter `~/.ssh/id_rsa`.
- Ausgeführtes Terraform-Setup aus Tag 07 (SonarQube VM läuft auf AWS EC2).
- Lokal installierte Werkzeuge:
  - `ansible` & `boto3` / `botocore` (`pip install boto3 botocore`)
  - Ansible AWS Collection (`ansible-galaxy collection install amazon.aws`)

---

## Aufgabenstellung: Schritt-für-Schritt Erweiterung

### 1. Terraform Security Group anpassen (`sonarqube-vm.tf`)

Erweitern Sie das Terraform-Manifest aus Tag 07 (`sonarqube-vm.tf`), um die Ports für die Monitoring-Dienste freizuschalten:

- **Grafana**: Port `3000` (TCP)
- **Prometheus**: Port `9090` (TCP)
- **cAdvisor**: Port `8080` und/oder `8090` (TCP)

Ergänzen Sie in `sonarqube-vm.tf` unter `resource "aws_security_group" "sonarqube"`:

```hcl
ingress {
  from_port   = 3000
  to_port     = 3000
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"] # Grafana
}

ingress {
  from_port   = 9090
  to_port     = 9090
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"] # Prometheus
}

```

Ergänzen Sie zusätzlich die entsprechenden Outputs für die URLs in Terraform:
```hcl
output "grafana_url" {
  value = "http://${aws_eip.sonarqube.public_ip}:3000"
}
output "prometheus_url" {
  value = "http://${aws_eip.sonarqube.public_ip}:9090"
}
```

---

### 2. AWS Dynamic Inventory konfigurieren (`aws_ec2.yml`)

Erstellen Sie die Datei `aws_ec2.yml`, um Instanzen dynamisch von AWS abzufragen:

```yaml
---
plugin: amazon.aws.aws_ec2
regions:
  - us-east-1

filters:
  instance-state-name: running
  tag:Name:
    - sonarqube
    - sonarqube-server

hostnames:
  - ip-address
  - dns-name
  - tag:Name

keyed_groups:
  - key: tags.Name
    prefix: tag_Name
  - key: tags.Name
    separator: ''
```

---

### 3. Ansible Konfiguration (`ansible.cfg`)

Erstellen Sie die Datei `ansible.cfg` im selben Verzeichnis:

```ini
[defaults]
inventory = aws_ec2.yml
remote_user = ubuntu
host_key_checking = False
private_key_file = ~/.ssh/id_rsa

[inventory]
enable_plugins = amazon.aws.aws_ec2, host_list, script, auto, yaml, ini, toml
```

---

### 4. Ansible Playbook erstellen (`playbook.yml`)

Es existiert ein zweistufiges Playbook `playbook.yml` das bis auf die 2 mit **TODO** markierten Tasks schon erledigt ist:

- **Play 1 (`hosts: localhost`)**:
  Führt `terraform apply -auto-approve` im Terraform-Verzeichnis (z. B. `../tag07` oder `./infra`) aus, um sicherzustellen, dass der Terraform-State synchron ist und die Security Group angepasst wurde.

- **Play 2 (`hosts: tag_Name_sonarqube_server:sonarqube`)**:
  Führt die Server-Konfiguration auf der Remote-VM durch:
  1. Apt Cache aktualisieren und Pakete installieren (`git`, `docker.io`, `docker-compose-v2`, `curl`).
  2. Docker Service aktivieren und starten.
  3. Benutzer `ubuntu` zur `docker`-Gruppe hinzufügen.
  4. **TODO**: Repository `https://gitlab.com/ser-cal/m169-scripts.git` nach `/home/ubuntu/m169-scripts` klonen.
  5. **TODO**: Systemd-Service `/etc/systemd/system/monitoring.service` für den Docker Compose Monitoring-Stack in `/home/ubuntu/m169-scripts/KN05_B` erstellen, aktivieren und starten.

---

## Durchführung & Überprüfung

1. **Dynamisches Inventory testen**:
   ```bash
   ansible-inventory -i aws_ec2.yml --list
   ```

2. **Ansible Playbook ausführen**:
   ```bash
   ansible-playbook playbook.yml
   ```

3. **Zugriff auf die Dienste im Browser testen**:
   - **cAdvisor**: `http://<VM-IP>:8080` (oder `:8090`)
   - **Prometheus**: `http://<VM-IP>:9090`
   - **Grafana**: `http://<VM-IP>:3000`

---

## Musterlösung

Die vollständige Referenzlösung befindet sich im Musterlösungs-Repository im Branch `day_10_solution`: https://github.com/tbzdevops/musterloesungen-praxisauftraege/tree/day_10_solution