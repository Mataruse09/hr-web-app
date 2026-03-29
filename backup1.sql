-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: hr_system
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `attendance`
--

DROP TABLE IF EXISTS `attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `company_id` int unsigned NOT NULL,
  `employee_id` int unsigned NOT NULL,
  `work_date` date NOT NULL,
  `check_in` time DEFAULT NULL,
  `check_out` time DEFAULT NULL,
  `status` enum('Present','Absent','Late','Half-Day','Work From Home','Holiday') DEFAULT 'Present',
  `working_hours` decimal(5,2) DEFAULT NULL,
  `notes` varchar(500) DEFAULT NULL,
  `recorded_by` int unsigned DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_attendance` (`company_id`,`employee_id`,`work_date`),
  KEY `fk_att_recorder` (`recorded_by`),
  KEY `idx_att_date` (`work_date`),
  KEY `idx_att_employee` (`employee_id`),
  KEY `idx_att_status` (`status`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `attendance_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `employees_core` (`id`) ON DELETE CASCADE,
  CONSTRAINT `attendance_ibfk_3` FOREIGN KEY (`recorded_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attendance`
--

LOCK TABLES `attendance` WRITE;
/*!40000 ALTER TABLE `attendance` DISABLE KEYS */;
/*!40000 ALTER TABLE `attendance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `companies`
--

DROP TABLE IF EXISTS `companies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `companies` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `industry` varchar(100) DEFAULT NULL,
  `address` text,
  `phone` varchar(30) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `website` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_company_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `companies`
--

LOCK TABLES `companies` WRITE;
/*!40000 ALTER TABLE `companies` DISABLE KEYS */;
INSERT INTO `companies` VALUES (1,'TechCorp Inc.','Technology','123 Silicon Valley, CA 94000','555-0100','hr@techcorp.com','www.techcorp.com',1,'2026-03-28 19:51:04','2026-03-28 19:51:04');
/*!40000 ALTER TABLE `companies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `compensation`
--

DROP TABLE IF EXISTS `compensation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `compensation` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `company_id` int unsigned NOT NULL,
  `employee_id` int unsigned NOT NULL,
  `basic_salary` decimal(15,2) NOT NULL DEFAULT '0.00',
  `housing_allowance` decimal(15,2) NOT NULL DEFAULT '0.00',
  `transport_allowance` decimal(15,2) NOT NULL DEFAULT '0.00',
  `meal_allowance` decimal(15,2) NOT NULL DEFAULT '0.00',
  `other_allowances` decimal(15,2) NOT NULL DEFAULT '0.00',
  `income_tax_rate` decimal(5,2) NOT NULL DEFAULT '15.00' COMMENT 'Percentage e.g. 15 = 15%',
  `social_insurance` decimal(15,2) NOT NULL DEFAULT '0.00',
  `health_insurance` decimal(15,2) NOT NULL DEFAULT '0.00',
  `other_deductions` decimal(15,2) NOT NULL DEFAULT '0.00',
  `currency` char(3) NOT NULL DEFAULT 'USD',
  `effective_date` date NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_comp_company` (`company_id`),
  KEY `idx_comp_employee` (`employee_id`),
  KEY `idx_comp_effective` (`effective_date`),
  CONSTRAINT `compensation_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `compensation_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `employees_core` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compensation`
--

LOCK TABLES `compensation` WRITE;
/*!40000 ALTER TABLE `compensation` DISABLE KEYS */;
INSERT INTO `compensation` VALUES (1,1,1,85000.00,12000.00,6000.00,2400.00,0.00,22.00,4250.00,1700.00,0.00,'USD','2024-01-01','2026-03-28 19:51:06','2026-03-28 19:51:06'),(2,1,2,55000.00,8000.00,4800.00,1600.00,0.00,20.00,2750.00,1100.00,0.00,'USD','2024-01-01','2026-03-28 19:51:06','2026-03-28 19:51:06'),(3,1,3,72000.00,10000.00,5400.00,2000.00,0.00,21.00,3600.00,1440.00,0.00,'USD','2024-01-01','2026-03-28 19:51:06','2026-03-28 19:51:06'),(4,1,4,90000.00,13000.00,7200.00,2600.00,0.00,23.00,4500.00,1800.00,0.00,'USD','2024-01-01','2026-03-28 19:51:06','2026-03-28 19:51:06'),(5,1,5,60000.00,9000.00,5000.00,1800.00,0.00,20.00,3000.00,1200.00,0.00,'USD','2024-01-01','2026-03-28 19:51:06','2026-03-28 19:51:06'),(6,1,6,78000.00,11000.00,6000.00,2200.00,0.00,21.00,3900.00,1560.00,0.00,'USD','2024-01-01','2026-03-28 19:51:06','2026-03-28 19:51:06'),(7,1,7,82000.00,12000.00,6000.00,2400.00,0.00,22.00,4100.00,1640.00,0.00,'USD','2024-01-01','2026-03-28 19:51:06','2026-03-28 19:51:06'),(8,1,8,58000.00,8500.00,4800.00,1700.00,0.00,20.00,2900.00,1160.00,0.00,'USD','2024-01-01','2026-03-28 19:51:06','2026-03-28 19:51:06');
/*!40000 ALTER TABLE `compensation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `departments`
--

DROP TABLE IF EXISTS `departments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `departments` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `company_id` int unsigned NOT NULL,
  `name` varchar(150) NOT NULL,
  `description` text,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_dept_company` (`company_id`),
  CONSTRAINT `departments_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `departments`
--

LOCK TABLES `departments` WRITE;
/*!40000 ALTER TABLE `departments` DISABLE KEYS */;
INSERT INTO `departments` VALUES (1,1,'Human Resources','People operations and talent management','2026-03-28 19:51:04'),(2,1,'Engineering','Software development and infrastructure','2026-03-28 19:51:04'),(3,1,'Finance','Accounting, budgeting and financial planning','2026-03-28 19:51:04'),(4,1,'Sales & Marketing','Revenue generation and brand strategy','2026-03-28 19:51:04'),(5,1,'Operations','Daily operations and process management','2026-03-28 19:51:04');
/*!40000 ALTER TABLE `departments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `employees_core`
--

DROP TABLE IF EXISTS `employees_core`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employees_core` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `company_id` int unsigned NOT NULL,
  `employee_code` varchar(50) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `phone` varchar(30) DEFAULT NULL,
  `department_id` int unsigned DEFAULT NULL,
  `job_title` varchar(150) DEFAULT NULL,
  `employment_type` enum('Full-Time','Part-Time','Contract','Intern') DEFAULT 'Full-Time',
  `status` enum('Active','Inactive','Terminated','On Leave') DEFAULT 'Active',
  `hire_date` date NOT NULL,
  `termination_date` date DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `gender` enum('Male','Female','Other','Prefer not to say') DEFAULT 'Prefer not to say',
  `nationality` varchar(100) DEFAULT NULL,
  `address` text,
  `emergency_contact_name` varchar(200) DEFAULT NULL,
  `emergency_contact_phone` varchar(30) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_emp_code_company` (`company_id`,`employee_code`),
  KEY `idx_emp_company` (`company_id`),
  KEY `idx_emp_status` (`status`),
  KEY `idx_emp_department` (`department_id`),
  KEY `idx_emp_hire_date` (`hire_date`),
  CONSTRAINT `employees_core_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `employees_core_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employees_core`
--

LOCK TABLES `employees_core` WRITE;
/*!40000 ALTER TABLE `employees_core` DISABLE KEYS */;
INSERT INTO `employees_core` VALUES (1,1,'EMP001','John','Smith','john.smith@techcorp.com','555-0101',2,'Senior Developer','Full-Time','Active','2022-03-15',NULL,'1990-05-12','Male','American',NULL,NULL,NULL,'2026-03-28 19:51:06','2026-03-28 19:51:06'),(2,1,'EMP002','Emily','Davis','emily.davis@techcorp.com','555-0102',2,'Junior Developer','Full-Time','Active','2023-01-10',NULL,'1997-08-22','Female','American',NULL,NULL,NULL,'2026-03-28 19:51:06','2026-03-28 19:51:06'),(3,1,'EMP003','Robert','Wilson','r.wilson@techcorp.com','555-0103',3,'Financial Analyst','Full-Time','Active','2021-07-20',NULL,'1988-11-03','Male','British',NULL,NULL,NULL,'2026-03-28 19:51:06','2026-03-28 19:51:06'),(4,1,'EMP004','Jennifer','Brown','j.brown@techcorp.com','555-0104',4,'Sales Manager','Full-Time','Active','2020-11-05',NULL,'1985-02-17','Female','Canadian',NULL,NULL,NULL,'2026-03-28 19:51:06','2026-03-28 19:51:06'),(5,1,'EMP005','David','Taylor','d.taylor@techcorp.com','555-0105',1,'HR Specialist','Full-Time','Active','2022-06-01',NULL,'1993-07-30','Male','American',NULL,NULL,NULL,'2026-03-28 19:51:06','2026-03-28 19:51:06'),(6,1,'EMP006','Amanda','Martinez','a.martinez@techcorp.com','555-0106',2,'DevOps Engineer','Full-Time','Active','2023-03-20',NULL,'1995-04-15','Female','Mexican',NULL,NULL,NULL,'2026-03-28 19:51:06','2026-03-28 19:51:06'),(7,1,'EMP007','Chris','Anderson','c.anderson@techcorp.com','555-0107',5,'Ops Manager','Full-Time','Active','2021-02-15',NULL,'1987-09-08','Male','Australian',NULL,NULL,NULL,'2026-03-28 19:51:06','2026-03-28 19:51:06'),(8,1,'EMP008','Lisa','Thomas','l.thomas@techcorp.com','555-0108',4,'Marketing Spec.','Full-Time','Active','2022-09-12',NULL,'1994-12-20','Female','American',NULL,NULL,NULL,'2026-03-28 19:51:06','2026-03-28 19:51:06');
/*!40000 ALTER TABLE `employees_core` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leave_balances`
--

DROP TABLE IF EXISTS `leave_balances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leave_balances` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `company_id` int unsigned NOT NULL,
  `employee_id` int unsigned NOT NULL,
  `year` year NOT NULL,
  `annual_total` int NOT NULL DEFAULT '21',
  `annual_used` int NOT NULL DEFAULT '0',
  `sick_total` int NOT NULL DEFAULT '14',
  `sick_used` int NOT NULL DEFAULT '0',
  `emergency_total` int NOT NULL DEFAULT '5',
  `emergency_used` int NOT NULL DEFAULT '0',
  `other_used` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_balance_year` (`company_id`,`employee_id`,`year`),
  KEY `idx_balance_employee` (`employee_id`),
  CONSTRAINT `leave_balances_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `leave_balances_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `employees_core` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leave_balances`
--

LOCK TABLES `leave_balances` WRITE;
/*!40000 ALTER TABLE `leave_balances` DISABLE KEYS */;
INSERT INTO `leave_balances` VALUES (1,1,1,2026,21,1,14,0,5,0,0),(2,1,2,2026,21,6,14,3,5,0,0),(3,1,3,2026,21,3,14,5,5,0,0),(4,1,4,2026,21,5,14,5,5,0,0),(5,1,5,2026,21,8,14,1,5,0,0),(6,1,6,2026,21,7,14,0,5,0,0),(7,1,7,2026,21,4,14,0,5,0,0),(8,1,8,2026,21,2,14,5,5,0,0);
/*!40000 ALTER TABLE `leave_balances` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leave_requests`
--

DROP TABLE IF EXISTS `leave_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leave_requests` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `company_id` int unsigned NOT NULL,
  `employee_id` int unsigned NOT NULL,
  `leave_type` enum('Annual','Sick','Emergency','Maternity','Paternity','Unpaid','Other') NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `days_requested` int NOT NULL,
  `reason` text,
  `status` enum('Pending','Approved','Rejected','Cancelled') DEFAULT 'Pending',
  `reviewed_by` int unsigned DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  `review_notes` text,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_leave_company` (`company_id`),
  KEY `fk_leave_reviewer` (`reviewed_by`),
  KEY `idx_leave_employee` (`employee_id`),
  KEY `idx_leave_status` (`status`),
  KEY `idx_leave_dates` (`start_date`,`end_date`),
  CONSTRAINT `leave_requests_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `leave_requests_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `employees_core` (`id`) ON DELETE CASCADE,
  CONSTRAINT `leave_requests_ibfk_3` FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leave_requests`
--

LOCK TABLES `leave_requests` WRITE;
/*!40000 ALTER TABLE `leave_requests` DISABLE KEYS */;
/*!40000 ALTER TABLE `leave_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payroll_runs`
--

DROP TABLE IF EXISTS `payroll_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payroll_runs` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `company_id` int unsigned NOT NULL,
  `employee_id` int unsigned NOT NULL,
  `pay_period` varchar(7) NOT NULL COMMENT 'Format: YYYY-MM',
  `basic_salary` decimal(15,2) NOT NULL,
  `total_allowances` decimal(15,2) NOT NULL DEFAULT '0.00',
  `gross_salary` decimal(15,2) NOT NULL,
  `bonus` decimal(15,2) NOT NULL DEFAULT '0.00',
  `income_tax` decimal(15,2) NOT NULL DEFAULT '0.00',
  `total_deductions` decimal(15,2) NOT NULL DEFAULT '0.00',
  `net_salary` decimal(15,2) NOT NULL,
  `working_days` int NOT NULL DEFAULT '22',
  `present_days` int NOT NULL DEFAULT '0',
  `status` enum('Draft','Pending','Approved','Paid') NOT NULL DEFAULT 'Draft',
  `processed_by` int unsigned DEFAULT NULL,
  `processed_at` datetime DEFAULT NULL,
  `notes` text,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_payroll` (`company_id`,`employee_id`,`pay_period`),
  KEY `fk_pay_processor` (`processed_by`),
  KEY `idx_payroll_period` (`pay_period`),
  KEY `idx_payroll_status` (`status`),
  KEY `idx_payroll_employee` (`employee_id`),
  CONSTRAINT `payroll_runs_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `payroll_runs_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `employees_core` (`id`) ON DELETE CASCADE,
  CONSTRAINT `payroll_runs_ibfk_3` FOREIGN KEY (`processed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payroll_runs`
--

LOCK TABLES `payroll_runs` WRITE;
/*!40000 ALTER TABLE `payroll_runs` DISABLE KEYS */;
/*!40000 ALTER TABLE `payroll_runs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `performance_reviews`
--

DROP TABLE IF EXISTS `performance_reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `performance_reviews` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `company_id` int unsigned NOT NULL,
  `employee_id` int unsigned NOT NULL,
  `reviewer_id` int unsigned NOT NULL,
  `review_period` varchar(50) NOT NULL COMMENT 'e.g. Q1-2024, Annual-2024',
  `review_date` date NOT NULL,
  `overall_rating` decimal(3,1) NOT NULL COMMENT 'Scale 1.0 - 5.0',
  `goals_score` decimal(3,1) DEFAULT NULL,
  `communication` decimal(3,1) DEFAULT NULL,
  `teamwork` decimal(3,1) DEFAULT NULL,
  `technical_skills` decimal(3,1) DEFAULT NULL,
  `leadership` decimal(3,1) DEFAULT NULL,
  `strengths` text,
  `improvements` text,
  `comments` text,
  `status` enum('Draft','Submitted','Acknowledged') NOT NULL DEFAULT 'Draft',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_perf_company` (`company_id`),
  KEY `fk_perf_reviewer` (`reviewer_id`),
  KEY `idx_perf_employee` (`employee_id`),
  KEY `idx_perf_period` (`review_period`),
  KEY `idx_perf_date` (`review_date`),
  CONSTRAINT `performance_reviews_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `performance_reviews_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `employees_core` (`id`) ON DELETE CASCADE,
  CONSTRAINT `performance_reviews_ibfk_3` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `performance_reviews`
--

LOCK TABLES `performance_reviews` WRITE;
/*!40000 ALTER TABLE `performance_reviews` DISABLE KEYS */;
/*!40000 ALTER TABLE `performance_reviews` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `company_id` int unsigned NOT NULL,
  `username` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `email` varchar(150) NOT NULL,
  `full_name` varchar(200) NOT NULL,
  `role` enum('Admin','HR','CHRO') NOT NULL DEFAULT 'HR',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `last_login` datetime DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_username` (`username`),
  UNIQUE KEY `uq_email_company` (`company_id`,`email`),
  KEY `idx_user_company` (`company_id`),
  KEY `idx_user_role` (`role`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,1,'admin','$2b$12$ef1yuq86eqa2bUZcmStgMOZgLXpj.l7axVadbyT1sGaRCve4dFNnW','admin@techcorp.com','System Administrator','Admin',1,'2026-03-28 19:53:01','2026-03-28 19:51:06'),(2,1,'hr_manager','$2b$12$4z2tAisK8AbOWhq0LPmXY.PRribaDSG0SNqQYHDzd1w8TkKQLPQFe','hrmanager@techcorp.com','Sarah Johnson','HR',1,NULL,'2026-03-28 19:51:06'),(3,1,'chro','$2b$12$YmrfgyoV4NNX4t7xQLHFtev/sqr26XjZq.dAMgor6BnjvKiAykPNe','chro@techcorp.com','Michael Chen','CHRO',1,NULL,'2026-03-28 19:51:06');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-29 10:57:36
