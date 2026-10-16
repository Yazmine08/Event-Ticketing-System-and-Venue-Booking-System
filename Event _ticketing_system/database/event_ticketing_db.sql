-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: event_ticketing_db
-- ------------------------------------------------------
-- Server version	8.0.44

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
-- Table structure for table `bookings`
--

DROP TABLE IF EXISTS `bookings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bookings` (
  `booking_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `event_id` int NOT NULL,
  `quantity` int NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `booking_status` enum('pending','confirmed','cancelled') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `booking_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `ticket_code` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cancellation_reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cancelled_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`booking_id`),
  UNIQUE KEY `ticket_code` (`ticket_code`),
  KEY `user_id` (`user_id`),
  KEY `event_id` (`event_id`),
  CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `bookings_ibfk_2` FOREIGN KEY (`event_id`) REFERENCES `events` (`event_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bookings`
--

LOCK TABLES `bookings` WRITE;
/*!40000 ALTER TABLE `bookings` DISABLE KEYS */;
INSERT INTO `bookings` VALUES (1,4,1,2,240.00,'confirmed','2026-10-11 07:37:14','TKT001',NULL,NULL),(2,5,2,1,80.00,'confirmed','2026-10-11 07:37:14','TKT002',NULL,NULL),(3,4,3,3,150.00,'confirmed','2026-10-11 07:37:14','TKT003',NULL,NULL),(4,5,4,1,35.00,'confirmed','2026-10-11 07:37:14','TKT004',NULL,NULL),(5,4,5,2,200.00,'cancelled','2026-10-11 07:37:14','TKT005',NULL,NULL);
/*!40000 ALTER TABLE `bookings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `category_id` int NOT NULL AUTO_INCREMENT,
  `category_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `category_name` (`category_name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,'Music','Concerts and live performances'),(2,'Technology','Technology conferences and events'),(3,'Sports','Sports events and competitions'),(4,'Education','Workshops and educational programmes'),(5,'Business','Business conferences and networking');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `events`
--

DROP TABLE IF EXISTS `events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `events` (
  `event_id` int NOT NULL AUTO_INCREMENT,
  `organiser_id` int NOT NULL,
  `venue_id` int NOT NULL,
  `category_id` int NOT NULL,
  `event_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `event_date` date NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `ticket_price` decimal(10,2) NOT NULL,
  `total_tickets` int NOT NULL,
  `available_tickets` int NOT NULL,
  `event_status` enum('draft','published','cancelled','completed') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft',
  `image_url` mediumtext COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`event_id`),
  KEY `organiser_id` (`organiser_id`),
  KEY `venue_id` (`venue_id`),
  KEY `category_id` (`category_id`),
  CONSTRAINT `events_ibfk_1` FOREIGN KEY (`organiser_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `events_ibfk_2` FOREIGN KEY (`venue_id`) REFERENCES `venues` (`venue_id`) ON DELETE RESTRICT,
  CONSTRAINT `events_ibfk_3` FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `events`
--

LOCK TABLES `events` WRITE;
/*!40000 ALTER TABLE `events` DISABLE KEYS */;
INSERT INTO `events` VALUES (1,2,1,1,'Malaysia Music Festival','Live music festival featuring local artists','2026-11-15','18:00:00','23:00:00',120.00,2500,2498,'published','https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=800&q=80','2026-10-11 07:37:14'),(2,3,3,2,'Tech Innovation Conference','Conference about technology and innovation','2026-11-20','09:00:00','17:00:00',80.00,3000,3000,'published','https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&w=800&q=80','2026-10-11 07:37:14'),(3,2,2,3,'National Sports Championship','National indoor sports competition','2026-12-05','10:00:00','18:00:00',50.00,8000,7997,'published','https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=800&q=80','2026-10-11 07:37:14'),(4,3,4,4,'Digital Skills Workshop','Workshop on digital and technical skills','2026-12-12','09:00:00','16:00:00',35.00,500,499,'published','https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=800&q=80','2026-10-11 07:37:14'),(5,2,1,5,'Business Networking Summit','Networking event for entrepreneurs','2027-01-10','10:00:00','17:00:00',100.00,1500,1500,'published','https://images.unsplash.com/photo-1511578314322-379afb476865?auto=format&fit=crop&w=800&q=80','2026-10-11 07:37:14'),(6,2,6,1,'Coldplay: Music of the Spheres World Tour Live in KL','The iconic British rock band brings their record-breaking Music of the Spheres World Tour back to Kuala Lumpur for an unforgettable sustainable stadium experience featuring hits like Yellow, Fix You, and Viva La Vida.','2026-11-28','20:00:00','23:30:00',298.00,15000,14850,'published','https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=800&q=80','2026-10-15 02:14:36'),(7,3,6,1,'Ed Sheeran: Mathematics Tour (+ - = / x) Live in KL','Global singer-songwriter sensation Ed Sheeran performs in the round with cutting-edge 360-degree stage production with special guest Calum Scott.','2026-12-02','19:30:00','23:00:00',258.00,12000,11920,'published','https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=800&q=80','2026-10-15 02:14:36'),(8,2,2,1,'Bruno Mars Live in Concert Kuala Lumpur','Multi-Grammy winner Bruno Mars brings his signature showmanship, electric funk, pop, and soul hits including 24K Magic, Just the Way You Are, and Uptown Funk to Axiata Arena.','2026-12-18','20:30:00','23:30:00',398.00,10000,9840,'published','https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=800&q=80','2026-10-15 02:14:36'),(9,2,9,1,'Dato Sri Siti Nurhaliza: Love is in the Sky Concert','Malaysias beloved Queen of Voice Dato Sri Siti Nurhaliza serenades fans with an enchanting symphonic concert 6,000 feet above sea level at Genting Highlands.','2026-12-24','20:00:00','23:00:00',188.00,5000,4910,'published','https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=800&q=80','2026-10-15 02:14:36'),(10,3,7,1,'Search & Wings: Double Trouble Rock Legend Showcase','Legendary Malaysian rock pioneers Search and Wings unite on stage for an epic high-voltage celebration of Malay rock anthems that shaped generations.','2027-01-16','20:30:00','23:30:00',168.00,2400,2350,'published','https://images.unsplash.com/photo-1465847899084-d164df4dedc6?auto=format&fit=crop&w=800&q=80','2026-10-15 02:14:36'),(11,2,6,1,'A.R. Rahman Live in Concert KL: Symphony of Stars','The Mozart of Madras, Oscar and Grammy Award winner A.R. Rahman, brings a monumental 70-piece musical troupe to Bukit Jalil for an emotional three-hour musical voyage.','2027-01-23','19:00:00','23:00:00',228.00,14000,13800,'published','https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=800&q=80','2026-10-15 02:14:36'),(12,3,7,1,'RADWIMPS World Tour Live in Kuala Lumpur','Acclaimed Japanese rock innovators RADWIMPS, renowned worldwide for Makoto Shinkai anime scores Your Name and Weathering With You, perform live in an intimate venue experience.','2027-02-06','20:00:00','22:30:00',328.00,2200,2150,'published','https://images.unsplash.com/photo-1524368535928-5b5e00ddc76b?auto=format&fit=crop&w=800&q=80','2026-10-15 02:14:36'),(13,2,2,1,'IU: H.E.R. World Tour Live in Kuala Lumpur','K-Pop icon and chart-topping vocalist IU returns to Kuala Lumpur with her spellbinding live band and stunning cinematic visuals for the H.E.R. World Tour.','2027-02-20','19:30:00','22:30:00',388.00,9500,9380,'published','https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&w=800&q=80','2026-10-15 02:14:36'),(14,3,8,1,'Hausboom Music Fest: Malaysian Indie & Hip-Hop Summit','The biggest urban youth music festival in Malaysia uniting Masdo, Bunkface, Joe Flizzow, Noh Salleh, and Insomniacks for 8 hours of nonstop live Malaysian music.','2027-03-06','15:00:00','23:30:00',99.00,4500,4420,'published','https://images.unsplash.com/photo-1429962714451-bb934ecdc4ec?auto=format&fit=crop&w=800&q=80','2026-10-15 02:14:36');
/*!40000 ALTER TABLE `events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments`
--

DROP TABLE IF EXISTS `payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments` (
  `payment_id` int NOT NULL AUTO_INCREMENT,
  `booking_id` int NOT NULL,
  `payment_method` enum('online_banking','card','ewallet','cash') COLLATE utf8mb4_unicode_ci NOT NULL,
  `payment_amount` decimal(10,2) NOT NULL,
  `payment_status` enum('pending','paid','failed','refunded') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `transaction_reference` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `payment_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`payment_id`),
  UNIQUE KEY `transaction_reference` (`transaction_reference`),
  KEY `booking_id` (`booking_id`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`booking_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments`
--

LOCK TABLES `payments` WRITE;
/*!40000 ALTER TABLE `payments` DISABLE KEYS */;
INSERT INTO `payments` VALUES (1,1,'online_banking',240.00,'paid','TXN001','2026-10-11 07:37:14'),(2,2,'card',80.00,'paid','TXN002','2026-10-11 07:37:14'),(3,3,'ewallet',150.00,'paid','TXN003','2026-10-11 07:37:14'),(4,4,'online_banking',35.00,'paid','TXN004','2026-10-11 07:37:14'),(5,5,'card',200.00,'refunded','TXN005','2026-10-11 07:37:14');
/*!40000 ALTER TABLE `payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` enum('admin','organiser','customer') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'customer',
  `api_key` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `api_key` (`api_key`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Admin EventHub','admin@example.com','$2y$10$D6dgGiedtBmNG02rSwJg8OmXQT.USEOW93ouZr.d6OgKdR3J7I5jS','0121111111','admin','adm_live_key_9876543210abcdef','2026-10-11 07:37:14'),(2,'Aina Rahman','aina@example.com','$2y$10$D6dgGiedtBmNG02rSwJg8OmXQT.USEOW93ouZr.d6OgKdR3J7I5jS','0122222222','organiser','org_live_key_abcdef1234567890','2026-10-11 07:37:14'),(3,'Daniel Lee','daniel@example.com','$2y$10$D6dgGiedtBmNG02rSwJg8OmXQT.USEOW93ouZr.d6OgKdR3J7I5jS','0123333333','organiser','org_live_key_daniel23456789','2026-10-11 07:37:14'),(4,'Sarah Ahmad','sarah@example.com','$2y$10$D6dgGiedtBmNG02rSwJg8OmXQT.USEOW93ouZr.d6OgKdR3J7I5jS','0124444444','customer','cus_live_key_aaaabbbbccccdddd','2026-10-11 07:37:14'),(5,'Amir Hakim','amir@example.com','$2y$10$D6dgGiedtBmNG02rSwJg8OmXQT.USEOW93ouZr.d6OgKdR3J7I5jS','0125555555','customer','cus_live_key_amir1122334455','2026-10-11 07:37:14');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `venues`
--

DROP TABLE IF EXISTS `venues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `venues` (
  `venue_id` int NOT NULL AUTO_INCREMENT,
  `venue_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `location` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `capacity` int NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `approval_status` enum('pending','approved','rejected') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  PRIMARY KEY (`venue_id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `venues`
--

LOCK TABLES `venues` WRITE;
/*!40000 ALTER TABLE `venues` DISABLE KEYS */;
INSERT INTO `venues` VALUES (1,'KL Convention Centre','Kuala Lumpur',3000,'Convention and exhibition venue','approved'),(2,'Axiata Arena','Bukit Jalil',12000,'Indoor sports and entertainment arena','approved'),(3,'MITEC','Kuala Lumpur',5000,'Exhibition and conference centre','approved'),(4,'Dewan Merdeka','Kuala Lumpur',2000,'Multipurpose event hall','approved'),(5,'Sunway Convention Centre','Selangor',3500,'Convention and corporate event venue','pending'),(6,'National Stadium Bukit Jalil','Kuala Lumpur',85000,'Premier national stadium of Malaysia for world-class mega concerts and international spectacles','approved'),(7,'Zepp Kuala Lumpur','Bukit Bintang City Centre, KL',2500,'World-standard live concert music hall equipped with premier acoustic systems','approved'),(8,'Mega Star Arena KL','Sungei Wang Plaza, Kuala Lumpur',5000,'Centrally-located indoor concert arena hosting premier regional touring artists','approved'),(9,'Arena of Stars','Resorts World Genting, Pahang',5100,'Iconic mountaintop entertainment amphitheatre hosting international music legends','approved');
/*!40000 ALTER TABLE `venues` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-15 10:19:57
