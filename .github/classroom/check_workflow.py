#!/usr/bin/env python3
import os
import sys
from pathlib import Path

import yaml


def find_root():
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / ".github").is_dir():
            return p
        p = p.parent
    return Path(__file__).resolve().parent


ROOT = find_root()
RESULTS_FILE = os.environ.get("CLASSROOM_RESULTS")

PASS = 0
FAIL = 0


def record(status, description):
    if RESULTS_FILE:
        with open(RESULTS_FILE, "a", encoding="utf-8") as result_file:
            result_file.write(f"{status}\t{description}\n")


def check(description, condition, solution):
    global PASS, FAIL

    if condition:
        print(f"PASS: {description}")
        print(f"::notice title=PASS: {description}::Check erfolgreich bestanden")
        record("PASS", description)
        PASS += 1
    else:
        print(f"FAIL: {description}")
        print(f"::error title=FAIL: {description}::{solution}")
        record("FAIL", description)
        FAIL += 1


def check_step_1_terraform():
    """Step 1: Terraform Security Group & Outputs in sonarqube-vm.tf"""
    tf_files = list(ROOT.glob("*.tf")) + list(ROOT.glob("**/*.tf"))
    tf_file_exists = len(tf_files) > 0
    check(
        "Step 1: Terraform-Datei (sonarqube-vm.tf) existiert",
        tf_file_exists,
        "Erstelle oder übernehme die Datei sonarqube-vm.tf aus Tag 07.",
    )

    if not tf_file_exists:
        check(
            "Step 1: Security Group für Monitoring-Ports (3000, 9090) konfiguriert",
            False,
            "Füge Ingress-Regeln für Ports 3000 (Grafana) und 9090 (Prometheus) hinzu.",
        )
        check(
            "Step 1: Outputs für Grafana- und Prometheus-URLs konfiguriert",
            False,
            "Füge output \"grafana_url\" und output \"prometheus_url\" in sonarqube-vm.tf ein.",
        )
        return

    all_tf_content = ""
    for f in tf_files:
        all_tf_content += f.read_text(encoding="utf-8") + "\n"

    has_port_3000 = "3000" in all_tf_content
    has_port_9090 = "9090" in all_tf_content
    has_sg = "aws_security_group" in all_tf_content or "ingress" in all_tf_content
    check(
        "Step 1: Security Group für Monitoring-Ports (3000, 9090) konfiguriert",
        has_sg and has_port_3000 and has_port_9090,
        "Ergänze in sonarqube-vm.tf Ingress-Regeln für Port 3000 (Grafana) und Port 9090 (Prometheus).",
    )

    has_grafana_url = "grafana_url" in all_tf_content
    has_prometheus_url = "prometheus_url" in all_tf_content
    check(
        "Step 1: Outputs für Grafana- und Prometheus-URLs konfiguriert",
        has_grafana_url and has_prometheus_url,
        "Ergänze die Outputs 'grafana_url' und 'prometheus_url' in sonarqube-vm.tf.",
    )


def check_step_2_dynamic_inventory():
    """Step 2: AWS Dynamic Inventory in aws_ec2.yml"""
    inv_path = ROOT / "aws_ec2.yml"
    if not inv_path.exists():
        inv_path = ROOT / "aws_ec2.yaml"

    inv_exists = inv_path.exists()
    check(
        "Step 2: Dynamic Inventory Datei (aws_ec2.yml) existiert",
        inv_exists,
        "Erstelle die Datei aws_ec2.yml im Repo-Root.",
    )

    if not inv_exists:
        check(
            "Step 2: aws_ec2.yml nutzt Plugin 'amazon.aws.aws_ec2' und Region 'us-east-1'",
            False,
            "Konfiguriere plugin: amazon.aws.aws_ec2 und regions: [us-east-1].",
        )
        check(
            "Step 2: aws_ec2.yml Filter und Keyed Groups konfiguriert",
            False,
            "Konfiguriere filters (instance-state-name, tag:Name) und keyed_groups.",
        )
        return

    content = inv_path.read_text(encoding="utf-8")

    has_plugin = "amazon.aws.aws_ec2" in content or "aws_ec2" in content
    has_region = "us-east-1" in content
    check(
        "Step 2: aws_ec2.yml nutzt Plugin 'amazon.aws.aws_ec2' und Region 'us-east-1'",
        has_plugin and has_region,
        "Stelle sicher, dass 'plugin: amazon.aws.aws_ec2' und 'regions: - us-east-1' in aws_ec2.yml stehen.",
    )

    has_filters = "filters:" in content or "instance-state-name" in content
    has_sonarqube = "sonarqube" in content
    has_keyed = "keyed_groups:" in content
    check(
        "Step 2: aws_ec2.yml Filter und Keyed Groups konfiguriert",
        has_filters and has_sonarqube and has_keyed,
        "Konfiguriere filters (instance-state-name: running, tag:Name: sonarqube) sowie keyed_groups.",
    )


def check_step_3_ansible_config():
    """Step 3: Ansible Configuration in ansible.cfg"""
    cfg_path = ROOT / "ansible.cfg"
    cfg_exists = cfg_path.exists()
    check(
        "Step 3: Datei ansible.cfg existiert im Repo-Root",
        cfg_exists,
        "Erstelle die Datei ansible.cfg im Hauptverzeichnis.",
    )

    if not cfg_exists:
        check(
            "Step 3: ansible.cfg ist mit inventory=aws_ec2.yml und enable_plugins konfiguriert",
            False,
            "Setze inventory = aws_ec2.yml und enable_plugins = amazon.aws.aws_ec2 in ansible.cfg.",
        )
        return

    content = cfg_path.read_text(encoding="utf-8")
    has_inventory = "aws_ec2.yml" in content or "aws_ec2.yaml" in content
    has_user = "ubuntu" in content
    has_plugins = "amazon.aws.aws_ec2" in content or "aws_ec2" in content
    has_host_key = "host_key_checking" in content or "False" in content or "false" in content

    check(
        "Step 3: ansible.cfg ist mit inventory=aws_ec2.yml und enable_plugins konfiguriert",
        has_inventory and has_user and has_plugins and has_host_key,
        "Konfiguriere inventory = aws_ec2.yml, remote_user = ubuntu, host_key_checking = False und enable_plugins = amazon.aws.aws_ec2 in ansible.cfg.",
    )


def check_step_4_ansible_playbook():
    """Step 4: Ansible Playbook in playbook.yml"""
    play_path = ROOT / "playbook.yml"
    if not play_path.exists():
        play_path = ROOT / "playbook.yaml"

    play_exists = play_path.exists()
    check(
        "Step 4: Ansible Playbook (playbook.yml) existiert",
        play_exists,
        "Erstelle die Datei playbook.yml im Repo-Root.",
    )

    if not play_exists:
        check(
            "Step 4: Playbook enthält Play 1 mit localhost für Terraform Sync",
            False,
            "Füge Play 1 für hosts: localhost mit terraform apply ein.",
        )
        check(
            "Step 4: Playbook installiert Docker, Git und konfiguriert Gruppe docker",
            False,
            "Füge Tasks für apt (git, docker.io, docker-compose-v2), Docker Service & ubuntu in docker-Gruppe hinzu.",
        )
        check(
            "Step 4: Playbook klont Monitoring Repository",
            False,
            "Füge Task zum Klonen von https://gitlab.com/ser-cal/m169-scripts.git hinzu.",
        )
        check(
            "Step 4: Playbook erstellt und aktiviert Systemd-Service für Monitoring Stack in KN05_B",
            False,
            "Füge einen Task zur Erstellung von /etc/systemd/system/monitoring.service hinzu.",
        )
        return

    content = play_path.read_text(encoding="utf-8")

    has_localhost = "localhost" in content or "127.0.0.1" in content
    has_terraform = "terraform" in content
    check(
        "Step 4: Playbook enthält Play 1 mit localhost für Terraform Sync",
        has_localhost and has_terraform,
        "Erstelle Play 1 mit 'hosts: localhost', welches terraform apply ausführt.",
    )

    has_git = "git" in content
    has_docker = "docker" in content
    has_ubuntu_group = "ubuntu" in content or "group" in content or "usermod" in content
    check(
        "Step 4: Playbook installiert Docker, Git und konfiguriert Gruppe docker",
        has_git and has_docker and has_ubuntu_group,
        "Installiere Git, Docker (docker.io / docker-compose-v2) und füge den User ubuntu der docker-Gruppe hinzu.",
    )

    has_repo_url = "m169-scripts" in content or "gitlab.com" in content
    check(
        "Step 4: Playbook klont Monitoring Repository",
        has_repo_url,
        "Klone das Repository https://gitlab.com/ser-cal/m169-scripts.git nach /home/ubuntu/m169-scripts.",
    )

    has_systemd_service = (
        "systemd" in content
        and ("monitoring.service" in content or "service" in content)
        and "KN05_B" in content
    )
    check(
        "Step 4: Playbook erstellt und aktiviert Systemd-Service für Monitoring Stack in KN05_B",
        has_systemd_service,
        "Erstelle /etc/systemd/system/monitoring.service für WorkingDirectory=/home/ubuntu/m169-scripts/KN05_B und aktiviere diesen Service mit ansible.builtin.systemd.",
    )


def main():
    if RESULTS_FILE:
        Path(RESULTS_FILE).write_text("", encoding="utf-8")

    check_step_1_terraform()
    check_step_2_dynamic_inventory()
    check_step_3_ansible_config()
    check_step_4_ansible_playbook()

    print("")
    print("-----------------------------------------")
    print("Zusammenfassung")
    print("-----------------------------------------")
    print(f"Erfüllt: {PASS} Kriterien")
    print(f"Offen:   {FAIL} Kriterien")
    print("-----------------------------------------")

    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
