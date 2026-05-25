---
id: "devops-ansible-basics"
title: "Ansible Playbooks, Roles, and Inventory"
language: "yaml"
category: "devops"
subcategory: "configuration-management"
tags: ["ansible", "playbook", "role", "inventory", "automation", "configuration"]
version: "latest"
retrieval_hint: "Ansible playbook role inventory handler template variable automation configuration"
last_verified: "2026-05-24"
confidence: "high"
---

# Ansible Playbooks, Roles, and Inventory

## When to Use
- Configuring servers reproducibly without custom scripts
- Deploying applications across fleets of machines
- Managing user accounts, packages, and service configurations
- Orchestrating multi-node deployments with ordering and conditionals

## Standard Pattern

### Inventory File

```ini
# --- inventory/hosts.ini ---
[webservers]
web1.example.com ansible_host=10.0.1.10
web2.example.com ansible_host=10.0.1.11

[dbservers]
db1.example.com ansible_host=10.0.2.10 ansible_user=postgres

[all:vars]
ansible_user=deploy
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_private_key_file=~/.ssh/deploy_key
```

### Playbook

```yaml
# --- site.yml ---
---
- name: Configure web servers
  hosts: webservers
  become: true
  roles:
    - common
    - nginx
    - app

- name: Configure database servers
  hosts: dbservers
  become: true
  roles:
    - common
    - postgres
```

### Role Structure

```yaml
# --- roles/nginx/tasks/main.yml ---
---
- name: Install nginx
  ansible.builtin.apt:
    name: nginx
    state: present
  notify: Restart nginx

- name: Deploy nginx config
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    owner: root
    group: root
    mode: "0644"
    validate: "nginx -t -c %s"
  notify: Reload nginx

- name: Ensure nginx is running
  ansible.builtin.service:
    name: nginx
    state: started
    enabled: true

# --- roles/nginx/handlers/main.yml ---
---
- name: Restart nginx
  ansible.builtin.service:
    name: nginx
    state: restarted

- name: Reload nginx
  ansible.builtin.service:
    name: nginx
    state: reloaded

# --- roles/nginx/templates/nginx.conf.j2 ---
server {
    listen {{ nginx_port | default(80) }};
    server_name {{ server_name }};

    location / {
        proxy_pass http://{{ app_host }}:{{ app_port }};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Variables

```yaml
# --- group_vars/webservers.yml ---
---
nginx_port: 80
server_name: "example.com"
app_host: "127.0.0.1"
app_port: 8000

# --- host_vars/web1.example.com.yml ---
---
app_port: 8001  # Override for this specific host
```

## Common Mistakes

```yaml
# WRONG: Using shell module for everything
- name: Install package
  ansible.builtin.shell: apt-get install -y nginx

# CORRECT: Use the idempotent module
- name: Install package
  ansible.builtin.apt:
    name: nginx
    state: present
```

```yaml
# WRONG: Hardcoding values instead of using variables
- name: Deploy config
  ansible.builtin.template:
    src: app.conf.j2
    dest: "/etc/myapp/config.ini"  # Hardcoded path

# CORRECT: Use variables with defaults
- name: Deploy config
  ansible.builtin.template:
    src: app.conf.j2
    dest: "{{ app_config_path | default('/etc/myapp/config.ini') }}"
```

```yaml
# WRONG: Not using notify for service restarts
- name: Update config
  ansible.builtin.copy:
    src: new-config.conf
    dest: /etc/nginx/nginx.conf
- name: Force restart every run
  ansible.builtin.service:
    name: nginx
    state: restarted  # Restarts even when config unchanged

# CORRECT: Use notify to restart only when config changes
- name: Update config
  ansible.builtin.copy:
    src: new-config.conf
    dest: /etc/nginx/nginx.conf
  notify: Restart nginx
```

## Gotchas
- `become: true` applies to ALL tasks in a play — if you need mixed privilege, split into separate plays or use `become` per task
- Ansible 2.10+ requires fully qualified collection names (`ansible.builtin.apt` not just `apt`) — short names still work but generate deprecation warnings
- Variables in `group_vars` and `host_vars` are auto-loaded based on directory names matching inventory group/host names — typos silently fail
- Handlers run at the end of a play, not immediately — multiple notifies to the same handler only trigger it once
- `ansible.builtin.template` fails silently if the Jinja2 template has undefined variables and you haven't set `jinja2_strict: true`
- Vault-encrypted files (`ansible-vault encrypt`) require `--ask-vault-pass` at runtime — use `ansible-vault encrypt_string` for inline secrets
- Fact gathering (`gather_facts: true`) adds ~10 seconds per host — disable with `gather_facts: false` when you don't need system facts
- Roles are evaluated in order — putting `common` before `app` ensures dependencies (users, dirs) exist first

## Related
- devops/terraform/basics.md
- devops/docker/dockerfile-patterns.md
