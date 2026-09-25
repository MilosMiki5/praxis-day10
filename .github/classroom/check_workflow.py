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
            "Step 4: Task 'apt' aktualisiert Paket-Cache (update_cache)",
            False,
            "Füge einen Task mit ansible.builtin.apt (update_cache: yes) in Play 2 ein.",
        )
        check(
            "Step 4: Task 'apt' installiert erforderliche Pakete (git, docker.io, docker-compose-v2)",
            False,
            "Installiere Git, Docker (docker.io) und docker-compose-v2 mit apt.",
        )
        check(
            "Step 4: Task 'systemd' startet und aktiviert Docker-Dienst",
            False,
            "Stelle sicher, dass der Docker-Dienst mit ansible.builtin.systemd gestartet und aktiviert wird.",
        )
        check(
            "Step 4: Task 'user' fügt User ubuntu zur docker-Gruppe hinzu (append: yes)",
            False,
            "Füge den Benutzer ubuntu mit ansible.builtin.user zur Gruppe docker hinzu.",
        )
        check(
            "Step 4: Task 'git' klont Monitoring-Repository (m169-scripts)",
            False,
            "Klone das Repository https://gitlab.com/ser-cal/m169-scripts.git nach /home/ubuntu/m169-scripts.",
        )
        check(
            "Step 4: Task 'file' setzt Rechte/Owner für geklontes Repository",
            False,
            "Setze Rechte/Owner für /home/ubuntu/m169-scripts auf ubuntu.",
        )
        check(
            "Step 4: Task 'copy' erstellt /etc/systemd/system/monitoring.service für Stack in KN05_B",
            False,
            "Erstelle /etc/systemd/system/monitoring.service mit WorkingDirectory=/home/ubuntu/m169-scripts/KN05_B.",
        )
        check(
            "Step 4: Task 'systemd' aktiviert und startet Monitoring-Service",
            False,
            "Aktiviere und starte den Service monitoring mit ansible.builtin.systemd.",
        )
        return

    content = play_path.read_text(encoding="utf-8")

    plays = None
    try:
        plays = yaml.safe_load(content)
    except Exception as e:
        print(f"Warning: Could not parse {play_path.name} as YAML: {e}")

    all_tasks = []
    global_vars = {}

    if isinstance(plays, list):
        for play in plays:
            if isinstance(play, dict):
                p_vars = play.get("vars", {})
                if isinstance(p_vars, dict):
                    global_vars.update(p_vars)
                p_tasks = play.get("tasks", [])
                if isinstance(p_tasks, list):
                    for t in p_tasks:
                        if isinstance(t, dict):
                            all_tasks.append((t, play))

    def resolve(val):
        if not isinstance(val, str):
            return str(val) if val is not None else ""
        res = val
        for k, v in global_vars.items():
            if isinstance(v, str):
                res = res.replace(f"{{{{ {k} }}}}", v).replace(f"{{{{{k}}}}}", v)
        return res

    def task_has_module(task, mod_names):
        for m in mod_names:
            if m in task:
                return task[m]
        return None

    def is_truthy(v):
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return v != 0
        if isinstance(v, str):
            return v.lower() in ("yes", "true", "1", "on")
        return False

    # Check 1: Play 1 with localhost for Terraform Sync
    has_play1_tf = False
    if plays:
        for t, play in all_tasks:
            cmd_args = task_has_module(t, ["command", "ansible.builtin.command", "shell", "ansible.builtin.shell"])
            if cmd_args is not None:
                cmd_str = resolve(str(cmd_args))
                hosts = str(play.get("hosts", ""))
                conn = str(play.get("connection", ""))
                if ("terraform" in cmd_str and "apply" in cmd_str) and ("localhost" in hosts or "127.0.0.1" in hosts or "local" in conn):
                    has_play1_tf = True
                    break
    if not has_play1_tf:
        has_play1_tf = ("localhost" in content or "127.0.0.1" in content) and "terraform" in content and "apply" in content

    check(
        "Step 4: Playbook enthält Play 1 mit localhost für Terraform Sync",
        has_play1_tf,
        "Erstelle Play 1 mit 'hosts: localhost', welches terraform apply ausführt.",
    )

    # Check 2: Task 'apt' update_cache
    has_apt_update = False
    if plays:
        for t, _ in all_tasks:
            apt_args = task_has_module(t, ["apt", "ansible.builtin.apt"])
            if apt_args is not None:
                if isinstance(apt_args, dict) and is_truthy(apt_args.get("update_cache")):
                    has_apt_update = True
                    break
                elif "update_cache" in resolve(str(apt_args)):
                    has_apt_update = True
                    break
    if not has_apt_update:
        has_apt_update = "apt" in content and "update_cache" in content

    check(
        "Step 4: Task 'apt' aktualisiert Paket-Cache (update_cache)",
        has_apt_update,
        "Füge einen Task mit ansible.builtin.apt (update_cache: yes) in Play 2 ein.",
    )

    # Check 3: Task 'apt' installs required packages (git, docker.io, docker-compose-v2)
    has_apt_pkgs = False
    if plays:
        for t, _ in all_tasks:
            apt_args = task_has_module(t, ["apt", "ansible.builtin.apt"])
            if apt_args is not None:
                s_args = resolve(str(apt_args))
                if "git" in s_args and ("docker.io" in s_args or "docker" in s_args) and ("docker-compose-v2" in s_args or "docker-compose" in s_args):
                    has_apt_pkgs = True
                    break
    if not has_apt_pkgs:
        has_apt_pkgs = "git" in content and "docker" in content and ("docker-compose-v2" in content or "docker-compose" in content)

    check(
        "Step 4: Task 'apt' installiert erforderliche Pakete (git, docker.io, docker-compose-v2)",
        has_apt_pkgs,
        "Installiere Git, Docker (docker.io) und docker-compose-v2 mit apt.",
    )

    # Check 4: Task 'systemd' starts & enables Docker
    has_docker_svc = False
    if plays:
        for t, _ in all_tasks:
            sys_args = task_has_module(t, ["systemd", "ansible.builtin.systemd", "service", "ansible.builtin.service"])
            if sys_args is not None:
                s_args = resolve(str(sys_args))
                if isinstance(sys_args, dict):
                    name_val = resolve(str(sys_args.get("name", "")))
                    state_val = str(sys_args.get("state", ""))
                    enabled_val = sys_args.get("enabled")
                    if name_val == "docker" and state_val == "started" and is_truthy(enabled_val):
                        has_docker_svc = True
                        break
                elif "docker" in s_args and "started" in s_args:
                    has_docker_svc = True
                    break
    if not has_docker_svc:
        has_docker_svc = "docker" in content and "started" in content and "enabled" in content

    check(
        "Step 4: Task 'systemd' startet und aktiviert Docker-Dienst",
        has_docker_svc,
        "Stelle sicher, dass der Docker-Dienst mit ansible.builtin.systemd gestartet (state: started) und aktiviert (enabled: yes) wird.",
    )

    # Check 5: Task 'user' adds user to docker group
    has_user_grp = False
    if plays:
        for t, _ in all_tasks:
            usr_args = task_has_module(t, ["user", "ansible.builtin.user"])
            if usr_args is not None:
                s_args = resolve(str(usr_args))
                if isinstance(usr_args, dict):
                    grp_val = resolve(str(usr_args.get("groups", usr_args.get("group", ""))))
                    app_val = usr_args.get("append")
                    if "docker" in grp_val and is_truthy(app_val):
                        has_user_grp = True
                        break
                elif "docker" in s_args and ("append" in s_args or "groups" in s_args):
                    has_user_grp = True
                    break
    if not has_user_grp:
        has_user_grp = "docker" in content and ("ubuntu" in content or "app_user" in content) and ("groups" in content or "group" in content)

    check(
        "Step 4: Task 'user' fügt User ubuntu zur docker-Gruppe hinzu (append: yes)",
        has_user_grp,
        "Füge den Benutzer ubuntu (oder {{ app_user }}) mit ansible.builtin.user zur Gruppe docker hinzu (groups: docker, append: yes).",
    )

    # Check 6: Task 'git' clones monitoring repo
    has_git_clone = False
    if plays:
        for t, _ in all_tasks:
            git_args = task_has_module(t, ["git", "ansible.builtin.git"])
            if git_args is not None:
                s_args = resolve(str(git_args))
                if isinstance(git_args, dict):
                    repo_val = resolve(str(git_args.get("repo", "")))
                    dest_val = resolve(str(git_args.get("dest", "")))
                    if ("m169-scripts" in repo_val or "gitlab.com" in repo_val) and "m169-scripts" in dest_val:
                        has_git_clone = True
                        break
                elif ("m169-scripts" in s_args or "gitlab.com" in s_args) and "m169-scripts" in s_args:
                    has_git_clone = True
                    break
    if not has_git_clone:
        has_git_clone = ("m169-scripts" in content or "gitlab.com" in content) and "git" in content

    check(
        "Step 4: Task 'git' klont Monitoring-Repository (m169-scripts)",
        has_git_clone,
        "Klone das Repository https://gitlab.com/ser-cal/m169-scripts.git nach /home/ubuntu/m169-scripts mit ansible.builtin.git.",
    )

    # Check 7: Task 'file' sets ownership on cloned repo
    has_file_owner = False
    if plays:
        for t, _ in all_tasks:
            file_args = task_has_module(t, ["file", "ansible.builtin.file"])
            if file_args is not None:
                s_args = resolve(str(file_args))
                if isinstance(file_args, dict):
                    path_val = resolve(str(file_args.get("path", "")))
                    owner_val = resolve(str(file_args.get("owner", "")))
                    group_val = resolve(str(file_args.get("group", "")))
                    if "m169-scripts" in path_val and ("ubuntu" in owner_val or "app_user" in owner_val):
                        has_file_owner = True
                        break
                elif "m169-scripts" in s_args and "owner" in s_args:
                    has_file_owner = True
                    break
    if not has_file_owner:
        has_file_owner = "file" in content and "owner" in content and "m169-scripts" in content

    check(
        "Step 4: Task 'file' setzt Rechte/Owner für geklontes Repository",
        has_file_owner,
        "Setze Rechte/Owner (owner: ubuntu, group: ubuntu) für /home/ubuntu/m169-scripts mit ansible.builtin.file.",
    )

    # Check 8: Task 'copy' creates systemd unit file monitoring.service in KN05_B
    has_copy_service = False
    if plays:
        for t, _ in all_tasks:
            copy_args = task_has_module(t, ["copy", "ansible.builtin.copy", "template", "ansible.builtin.template"])
            if copy_args is not None:
                s_args = resolve(str(copy_args))
                if isinstance(copy_args, dict):
                    dest_val = resolve(str(copy_args.get("dest", "")))
                    cnt_val = resolve(str(copy_args.get("content", "")))
                    if "monitoring.service" in dest_val and "KN05_B" in cnt_val and ("docker compose" in cnt_val or "docker-compose" in cnt_val or "ExecStart" in cnt_val):
                        has_copy_service = True
                        break
                elif "monitoring.service" in s_args and "KN05_B" in s_args:
                    has_copy_service = True
                    break
    if not has_copy_service:
        has_copy_service = "monitoring.service" in content and "KN05_B" in content and ("docker compose" in content or "docker-compose" in content)

    check(
        "Step 4: Task 'copy' erstellt /etc/systemd/system/monitoring.service für Stack in KN05_B",
        has_copy_service,
        "Erstelle /etc/systemd/system/monitoring.service mit WorkingDirectory=/home/ubuntu/m169-scripts/KN05_B und ExecStart=/usr/bin/docker compose up -d.",
    )

    # Check 9: Task 'systemd' enables & starts monitoring service
    has_monitoring_svc = False
    if plays:
        for t, _ in all_tasks:
            sys_args = task_has_module(t, ["systemd", "ansible.builtin.systemd", "service", "ansible.builtin.service"])
            if sys_args is not None:
                s_args = resolve(str(sys_args))
                if isinstance(sys_args, dict):
                    name_val = resolve(str(sys_args.get("name", "")))
                    state_val = str(sys_args.get("state", ""))
                    enabled_val = sys_args.get("enabled")
                    if name_val == "monitoring" and state_val == "started" and is_truthy(enabled_val):
                        has_monitoring_svc = True
                        break
                elif "monitoring" in s_args and "started" in s_args:
                    has_monitoring_svc = True
                    break
    if not has_monitoring_svc:
        has_monitoring_svc = "monitoring" in content and "systemd" in content and "started" in content

    check(
        "Step 4: Task 'systemd' aktiviert und startet Monitoring-Service",
        has_monitoring_svc,
        "Aktiviere und starte den Service 'monitoring' (state: started, enabled: true) mit ansible.builtin.systemd.",
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
