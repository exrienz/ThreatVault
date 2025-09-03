# **Introducing Sentinel**  

Welcome to the future of vulnerability management with **Sentinel**—a cutting-edge solution designed for the IT Security Engineer/Manger/DevSecOps Engineer. Sentinel streamlines the management of vulnerabilities reported by Nessus Pro,and multiple tools to deliver unparalleled deduplication, sla tracker, efficiency, accuracy, reliability and single point of vulnerability and compliance reporting in one platform  

[![Security Rating](https://sast.code-x.my/api/project_badges/measure?project=paynet-sentinel&metric=software_quality_security_rating&token=sqb_36e10a7c7571656f8b7f09a24ce5afb460b8a007)](https://sast.code-x.my/dashboard?id=paynet-sentinel)  [![Quality Gate Status](https://sast.code-x.my/api/project_badges/measure?project=paynet-sentinel&metric=alert_status&token=sqb_36e10a7c7571656f8b7f09a24ce5afb460b8a007)](https://sast.code-x.my/dashboard?id=paynet-sentinel)  [![Reliability Rating](https://sast.code-x.my/api/project_badges/measure?project=paynet-sentinel&metric=software_quality_reliability_rating&token=sqb_36e10a7c7571656f8b7f09a24ce5afb460b8a007)](https://sast.code-x.my/dashboard?id=paynet-sentinel)  [![Maintainability Rating](https://sast.code-x.my/api/project_badges/measure?project=paynet-sentinel&metric=software_quality_maintainability_rating&token=sqb_36e10a7c7571656f8b7f09a24ce5afb460b8a007)](https://sast.code-x.my/dashboard?id=paynet-sentinel)  

---

## **Why We Move Away from DefectDojo?**  

Our experience with DefectDojo revealed several critical challenges:  

- **Inconsistent Findings**: Misrepresentation of Nessus Pro findings led to host count discrepancies and delayed resolutions.  
- **Persistent Vulnerabilities**: Resolved findings often remained open, leading to inaccurate security metrics.  
- **Manual Overload**: Handling large numbers of findings manually wasted resources and delayed security initiatives.  
- **Limited Support**: DefectDojo’s open-source nature meant inadequate support, leading to operational inefficiencies.  

These issues increased the risk of SLA breaches and weakened overall security posture.  

---

## **Why Choose Sentinel?**  

### **1. Accurate Integration**  
Effortlessly track vulnerabilities from Nessus Pro with precise host counts and CVE mappings.  

### **2. Automated Closure**  
Sentinel intelligently resolves findings, reducing manual efforts and ensuring data accuracy.  

### **3. Enhanced Efficiency**  
Automates repetitive workflows, allowing teams to focus on proactive security tasks.  

### **4. Comprehensive Support**  
A dedicated support team ensures a seamless experience for all users.  

With **Sentinel**, efficiency, reliability, and control converge to redefine vulnerability management.  

---



#### **Sentinel's Method**  
- **Finding A, 192.168.0.1, Port 80, CVE-2024-6651**  
- **Finding A, 192.168.0.2, Port 80, CVE-2024-6651**  
- **Finding A, 192.168.0.1, Port 81, CVE-2024-6651**  
- **Finding A, 192.168.0.1, Port 80, CVE-2024-6652**  

This approach enhances accuracy and visibility, resulting in more actionable findings.  

---

## **User Roles in Sentinel**  

Sentinel accommodates multiple user roles, ensuring flexibility for future adjustments:  

- **Administrator**  
  - Manages admin accounts and performs all ITSE tasks.  
  - Oversees administrative functions.  

- **ITSE (Information Technology Security Engineer)**  
  - Approves user accounts for management and owners.  
  - Assigns project ownership and manages scan data.  

- **Management (CISO, Management Team)**  
  - View-only access to dashboards and findings.  

- **Owner (Product Owners)**  
  - View-only access to findings for assigned products.  

---

## **Getting Started with Sentinel**  

### **1. Clone the Repository**  
```bash  
git clone <repository_url>  
cd <repository_directory>  
```  


### **2. Build and Deploy**  
```bash  
docker-compose up --build  
```  

### **3. Access the Application**  
Check the `.env.` file for `APP_URL` or port configuration, then access Sentinel via a web browser.  




Sentinel empowers security teams with **automation, precision, and efficiency**. Get started today and take control of your vulnerability management process!  

