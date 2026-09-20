-- Official-shaped MySQL slice that also contains prefixed sibling tables.
-- `gcd_issue_credit` / `gcd_series_bond` share ids with real issue/series
-- rows. The loader must not treat those as `gcd_issue` / `gcd_series`.
-- Lives in a subdirectory so dump-dir globs of gcd-dump-sql/ still see only
-- the original slice.sql fixture.
CREATE TABLE `gcd_publisher` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
);
INSERT INTO `gcd_publisher` VALUES (78,'Marvel',0);

CREATE TABLE `gcd_series` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `year_began` int DEFAULT NULL,
  `publisher_id` int NOT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
);
INSERT INTO `gcd_series` VALUES (2121,'Fantastic Four',1961,78,0);

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
(40775,'285',2121,'December 1985','1985-12-00','1985-09-17','0.65 USD','','','',NULL,'Direct','',285,0);

CREATE TABLE `gcd_series_bond` (
  `id` int NOT NULL,
  `origin_id` int NOT NULL,
  `target_id` int NOT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
);
INSERT INTO `gcd_series_bond` VALUES (2121,2121,9999,0);

CREATE TABLE `gcd_issue_credit` (
  `id` int NOT NULL,
  `creator_id` int NOT NULL,
  `credit_type_id` int NOT NULL,
  `issue_id` int NOT NULL,
  `deleted` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
);
INSERT INTO `gcd_issue_credit` VALUES (40775,1,1,40775,0);

CREATE TABLE `gcd_issue_brand_emblem` (
  `id` int NOT NULL,
  `issue_id` int NOT NULL,
  `brand_id` int NOT NULL,
  PRIMARY KEY (`id`)
);
INSERT INTO `gcd_issue_brand_emblem` (`id`,`issue_id`,`brand_id`) VALUES (40775,40775,1);
