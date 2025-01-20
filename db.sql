-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: us.mysql.db.bot-hosting.net
-- Generation Time: 27-Dec-2023 at 02:06
-- Server version: 10.4.25-MariaDB
-- PHP version: 8.1.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

-- Preserve previous settings
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `animalia_bot`
--
CREATE DATABASE IF NOT EXISTS `animalia_bot` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `animalia_bot`;

-- --------------------------------------------------------

--
-- Table structure for `players`
--

CREATE TABLE IF NOT EXISTS `players` (
  `steam_id` varchar(255) NOT NULL,
  `discord_id` varchar(255) DEFAULT NULL,
  `bugs` int(11) DEFAULT NULL,
  `animals` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`animals`)),
  `last_work_time` datetime DEFAULT NULL,
  `bugs_received` tinyint(4) NOT NULL DEFAULT 0,
  `last_voice_time` datetime DEFAULT NULL,
  `voice_start_time` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Add missing columns if needed
ALTER TABLE `players`
  ADD COLUMN IF NOT EXISTS `last_work_time` datetime DEFAULT NULL;

-- --------------------------------------------------------

--
-- Trigger for awarding bugs after link
--
DELIMITER $$
CREATE TRIGGER IF NOT EXISTS `award_bugs_after_link` 
AFTER UPDATE ON `players`
FOR EACH ROW 
BEGIN
    IF NEW.bugs_received = 1 AND OLD.bugs_received = 0 THEN
        -- Award 75k bugs to the user's balance
        UPDATE players
        SET bugs = bugs + 75000
        WHERE discord_id = NEW.discord_id;
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for `strikes`
--

CREATE TABLE IF NOT EXISTS `strikes` (
  `id` int(11) NOT NULL,
  `date_issued` timestamp NOT NULL DEFAULT current_timestamp(),
  `admin_id` varchar(255) DEFAULT NULL,
  `player_steam_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for `warnings`
--

CREATE TABLE IF NOT EXISTS `warnings` (
  `id` int(11) NOT NULL,
  `player_id` varchar(255) DEFAULT NULL,
  `reason` varchar(255) DEFAULT NULL,
  `warning_date` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Indices for dumped tables
--

-- Indices for table `players`
ALTER TABLE `players`
  ADD PRIMARY KEY IF NOT EXISTS (`steam_id`);

-- Indices for table `strikes`
ALTER TABLE `strikes`
  ADD PRIMARY KEY IF NOT EXISTS (`id`);

-- Indices for table `warnings`
ALTER TABLE `warnings`
  ADD PRIMARY KEY IF NOT EXISTS (`id`);

-- --------------------------------------------------------

--
-- Auto-increment values for tables
--

-- Auto-increment for table `strikes`
ALTER TABLE `strikes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

-- Auto-increment for table `warnings`
ALTER TABLE `warnings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=50;

COMMIT;

-- Restore previous settings
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
