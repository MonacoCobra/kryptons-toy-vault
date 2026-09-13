-- Tiny official-shaped MySQL slice for parser tests (not a live comics.org pull).
CREATE TABLE `gcd_publisher` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
);
INSERT INTO `gcd_publisher` VALUES (54,'Image Comics',0);

CREATE TABLE `gcd_series` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `year_began` int DEFAULT NULL,
  `publisher_id` int NOT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
);
INSERT INTO `gcd_series` VALUES (900101,'GCD Fixture Indie',2020,54,0);

CREATE TABLE `gcd_issue` (
  `id` int NOT NULL,
  `number` varchar(50) NOT NULL,
  `series_id` int NOT NULL,
  `publication_date` varchar(255) DEFAULT NULL,
  `key_date` varchar(10) DEFAULT NULL,
  `on_sale_date` varchar(10) DEFAULT NULL,
  `price` varchar(255) DEFAULT NULL,
  `barcode` varchar(38) DEFAULT NULL,
  `isbn` varchar(32) DEFAULT NULL,
  `valid_isbn` varchar(13) DEFAULT NULL,
  `variant_of_id` int DEFAULT NULL,
  `variant_name` varchar(255) DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `sort_code` int DEFAULT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
);
INSERT INTO `gcd_issue` VALUES
(8000001,'1',900101,'March 2020','2020-03-00','2020-03-11','3.99 USD','84428400999100111','','',NULL,'','',1,0),
(8000002,'2',900101,'April 2020','2020-04-00','2020-04-08','3.99 USD','','','',NULL,'','',2,0);
