# Tag 07 - Test Automation: SonarQube Deployment

Musterlösung für den Praxisauftrag: SonarQube Community Edition auf EC2 VM mit Docker Compose deployen.

## Dateien

- **sonarqube-vm.tf** - Terraform-Konfiguration für AWS Infrastruktur
  - EC2 Instance (t3.large)
  - Security Group (SSH + SonarQube Port)
  - Elastic IP für statische Adresse
  - Dynamische Ubuntu 24.04 AMI Suche

- **cloud-init.yml** - Cloud-Init Script für automatisierte Installation
  - Docker & Docker Compose Installation
  - PostgreSQL + SonarQube via docker-compose
  - Automatischer Start nach VM-Startup

## Verwendung

```bash
# Dateien herunterladen
curl -O https://raw.githubusercontent.com/tbzdevops/musterloesungen-praxisauftraege/main/tag07/sonarqube-vm.tf
curl -O https://raw.githubusercontent.com/tbzdevops/musterloesungen-praxisauftraege/main/tag07/cloud-init.yml

# Terraform ausführen
terraform init
terraform apply

# Nach ~7-8 Minuten ist SonarQube erreichbar unter:
# http://<ELASTIC-IP>:9000
```

## Credentials

- Benutzer: `admin`
- Passwort: `admin` (sollte nach Setup geändert werden)
- PostgreSQL Benutzer: `sonar`
- PostgreSQL Passwort: `sonarpassword123`

## Cleanup

```bash
terraform destroy
```
