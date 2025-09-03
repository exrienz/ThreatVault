
<p align="center">
  <img src="https://via.placeholder.com/900x150/4B6CB7/182848?text=Sentinel+%7C+Sponsored+by+PayNet&fontsize=36" alt="Sentinel Banner" />
</p>

# 🔒 Sentinel - Vulnerability Management Platform

[![Quality Gate Status](https://sast.code-x.my/api/project_badges/measure?project=sentinel&metric=alert_status&token=sqb_5a886e63b5dedd22d5458c17e86a8293de2a4a0f)](https://sast.code-x.my/dashboard?id=sentinel)
[![Security Rating](https://sast.code-x.my/api/project_badges/measure?project=sentinel&metric=software_quality_security_rating&token=sqb_5a886e63b5dedd22d5458c17e86a8293de2a4a0f)](https://sast.code-x.my/dashboard?id=sentinel)
[![Maintainability Rating](https://sast.code-x.my/api/project_badges/measure?project=sentinel&metric=software_quality_maintainability_rating&token=sqb_5a886e63b5dedd22d5458c17e86a8293de2a4a0f)](https://sast.code-x.my/dashboard?id=sentinel)
[![Lines of Code](https://sast.code-x.my/api/project_badges/measure?project=sentinel&metric=ncloc&token=sqb_5a886e63b5dedd22d5458c17e86a8293de2a4a0f)](https://sast.code-x.my/dashboard?id=sentinel)

---

## 🌟 Overview

**Sentinel** is a **next-gen vulnerability management platform** for IT Security Engineers, DevSecOps, and Managers.

It centralizes findings from **Nessus Pro** and other tools to deliver:

* ✅ Deduplication of vulnerabilities
* ✅ SLA tracking & compliance reporting
* ✅ Automated workflows
* ✅ Centralized actionable dashboards

> 💡 **Pro Tip:** Centralizing vulnerabilities allows faster remediation and more accurate SLA compliance.

---

## 🚀 Key Features

| Feature                     | Description                             |
| --------------------------- | --------------------------------------- |
| 🔗 **Accurate Integration** | Full CVE & host mapping from Nessus Pro |
| 🤖 **Automated Closure**    | Intelligent resolution of findings      |
| ⚡ **Efficiency Boost**      | Reduces repetitive manual tasks         |
| 🛡 **Enterprise Support**   | Dedicated support from PayNet           |

---

## 🛠 How Sentinel Works

Refer to the table below, each of the entries will be considered as 1 finding

```text
Finding A, 192.168.0.1, Port 80, CVE-2024-6651
Finding A, 192.168.0.2, Port 80, CVE-2024-6651
Finding A, 192.168.0.1, Port 81, CVE-2024-6651
Finding A, 192.168.0.1, Port 80, CVE-2024-6652
```

✅ Deduplication & visibility
✅ Actionable intelligence for remediation

> ⚠️ **Note:** Each finding is mapped precisely to host, port, and CVE for SLA tracking.

---

## 👥 User Roles

| Role                               | Permissions                                  |
| ---------------------------------- | -------------------------------------------- |
| 🛠 **Administrator**               | Full system & user access                    |
| 🔒 **IT Security Engineer (ITSE)** | Manage users, assign ownership, manage scans |
| 👓 **Management (CISO/Execs)**     | View-only dashboards                         |
| 📦 **Product Owner**               | View-only access to assigned products        |

---

## 🏁 Getting Started

### 1️⃣ Clone Repo

```bash
git clone <repository_url>
cd <repository_directory>
```

### 2️⃣ Build & Deploy

```bash
docker-compose up --build
```

### 3️⃣ Access App

Visit `APP_URL` in `.env` via browser

> 💡 **Tip:** Use `docker-compose logs -f` to monitor startup logs.

---

## 💡 Contribution Opportunities

| Contributor Type             | Activities                                        |
| ---------------------------- | ------------------------------------------------- |
| 👩‍💻 **Developer**          | Add features, optimize code, improve integrations |
| 🕵️ **Security Researcher**  | Test CVE handling, report improvements            |
| 🌐 **Community**             | Provide feedback, share use cases                 |
| 📋 **Project Manager (Muz)** | Oversee roadmap & releases                        |

**Steps to contribute:**

1. Fork repo
2. Create a branch: `git checkout -b feature-name`
3. Commit: `git commit -m "Add feature"`
4. Push: `git push origin feature-name`
5. Open a Pull Request

> 🌟 All contributors are recognized in the contributors section.

---

## 👥 Contributors

| Name                                                                         | Role                |
| ---------------------------------------------------------------------------- | ------------------- |
| [Exrienz](https://www.linkedin.com/in/muzaffarmohamed/?originalSubdomain=my) | Project Manager     |
| [Alice Dev](https://github.com/alice)                                        | Developer           |
| [Bob Sec](https://github.com/bob)                                            | Security Researcher |

---

## 📝 License

MIT License – see LICENSE file for details

