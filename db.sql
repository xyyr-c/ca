CREATE DATABASE `CertAuth` DEFAULT CHARACTER SET = 'utf8mb4';
use CertAuth;
CREATE TABLE `cert_requests` (
  `req_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `created_time` DATETIME DEFAULT NULL COMMENT '创建时间',
  `modified_time` DATETIME DEFAULT NULL COMMENT '修改时间',
  `removed_time` DATETIME DEFAULT NULL COMMENT '删除时间',
  `uid` INT NOT NULL COMMENT '申请人ID',
  `status` TINYINT UNSIGNED NOT NULL COMMENT '状态：1-待审 2-通过 3-拒绝',
  `pub_key` TEXT NOT NULL COMMENT '公钥',
  `country_code` VARCHAR(20) DEFAULT NULL COMMENT '国家代码',
  `region` VARCHAR(255) DEFAULT NULL COMMENT '省/州',
  `city` VARCHAR(255) DEFAULT NULL COMMENT '城市',
  `company` VARCHAR(255) DEFAULT NULL COMMENT '组织',
  `department` VARCHAR(255) DEFAULT NULL COMMENT '部门',
  `full_name` VARCHAR(255) NOT NULL COMMENT '姓名',
  `email` VARCHAR(255) DEFAULT NULL COMMENT '邮箱',
  PRIMARY KEY (`req_id`),
  KEY `idx_removed` (`removed_time`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='证书表';

CREATE TABLE `issued_certs` (
  `cert_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `created_time` DATETIME DEFAULT NULL,
  `modified_time` DATETIME DEFAULT NULL,
  `removed_time` DATETIME DEFAULT NULL,
  `uid` INT NOT NULL COMMENT '持有人ID',
  `status` TINYINT UNSIGNED NOT NULL COMMENT '状态：1-有效 2-失效',
  `req_id` INT NOT NULL COMMENT '关联请求ID',
  `expires_at` DATETIME NOT NULL COMMENT '过期时间',
  PRIMARY KEY (`cert_id`),
  KEY `idx_removed` (`removed_time`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='已签发证书表';


CREATE TABLE `accounts` (
  `uid` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `created_time` DATETIME DEFAULT NULL,
  `username` VARCHAR(16) NOT NULL,
  `pass_hash` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) DEFAULT NULL,
  `role` TINYINT DEFAULT NULL COMMENT '角色：1-管理员',
  PRIMARY KEY (`uid`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='用户账户表';

-- 插入管理员账户（示例）
INSERT INTO `accounts` (
    `created_time`,
    `username`,
    `pass_hash`,
    `role`
) VALUES (
    NOW(),                    -- 创建时间为当前时间
    'admin',                  -- 用户名（需唯一）
    '$2b$12$95Dy1yaM/oP5gc.NZv8cdOm3wuEDVeonzp3hbhslKHglbmGJCs2Vy',   -- 密码哈希值（需使用加密算法如bcrypt生成）
    1                         -- 角色：1表示管理员
);



