-- Create skywalking database
CREATE TABLE IF NOT EXISTS `product` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'Primary Key',
  `name` varchar(255) DEFAULT NULL COMMENT 'Product Name',
  `price` decimal(10,2) DEFAULT NULL COMMENT 'Product Price',
  `stock` int(11) DEFAULT NULL COMMENT 'Inventory Stock',
  `description` varchar(500) DEFAULT NULL COMMENT 'Product Description',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation Time',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update Time',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Stock table for xiaozhou-stock service
CREATE TABLE IF NOT EXISTS `stock` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `product_id` bigint NOT NULL COMMENT 'Product ID',
  `product_name` varchar(255) DEFAULT NULL COMMENT 'Product name',
  `stock_quantity` int NOT NULL DEFAULT '0' COMMENT 'Current stock quantity',
  `reserved_stock` int NOT NULL DEFAULT '0' COMMENT 'Reserved stock quantity',
  `unit_price` decimal(10,2) DEFAULT NULL COMMENT 'Unit price',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Create time',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stock table';

