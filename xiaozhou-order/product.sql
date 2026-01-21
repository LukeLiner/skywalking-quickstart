CREATE TABLE `product` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'Primary Key',
  `name` varchar(255) DEFAULT NULL COMMENT 'Product Name',
  `price` decimal(10,2) DEFAULT NULL COMMENT 'Product Price',
  `stock` int(11) DEFAULT NULL COMMENT 'Inventory Stock',
  `description` varchar(500) DEFAULT NULL COMMENT 'Product Description',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation Time',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update Time',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;