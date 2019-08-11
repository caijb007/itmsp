/*
SQLyog Community v12.01 (32 bit)
MySQL - 5.7.21 
*********************************************************************
*/
/*!40101 SET NAMES utf8 */;
insert into `iuser_exgroup` (`group_ptr_id`, `comment`, `member_type`, `menu`) values('1','VM管理员','staff','[\"I001\", \"M002\",\"I00201\", \"I00202\", \"M003\", \"I00302\", \"I00303\", \"I00304\", \"I00305\", \"I00301\", \"I00306\", \"I00203\", \"M004\", \"I00401\", \"I00402\", \"M006\", \"M005\", \"M008\", \"M007\", \"M009\", \"I00901\", \"I00601\", \"M011\", \"I01101\", \"I01102\", \"I01103\", \"I01104\"]');
insert into `itmsp_datadict` (`id`, `app`, `setting_type`, `name`, `value`, `display`, `ext_attr`) values('2','itmsp','OPTION','catalogue','M002','用户管理','{\"parent\": \"M0\"}');
insert into `itmsp_datadict` (`id`, `app`, `setting_type`, `name`, `value`, `display`, `ext_attr`) values('3','itmsp','OPTION','catalogue','M003','云服务管理','{\"parent\": \"M0\"}');
insert into `itmsp_datadict` (`id`, `app`, `setting_type`, `name`, `value`, `display`, `ext_attr`) values('4','itmsp','OPTION','menu','I00201','用户配置','{\"parent\": \"M002\"}');
insert into `itmsp_datadict` (`id`, `app`, `setting_type`, `name`, `value`, `display`, `ext_attr`) values('5','itmsp','OPTION','menu','I00202','用户组配置','{\"parent\": \"M002\"}');
insert into `itmsp_datadict` (`id`, `app`, `setting_type`, `name`, `value`, `display`, `ext_attr`) values('6','itmsp','OPTION','menu','I00301','云服务操作','{\"parent\": \"M002\"}');
insert into `itmsp_datadict` (`id`, `app`, `setting_type`, `name`, `value`, `display`, `ext_attr`) values('1','itmsp','OPTION','catalogue','M0','根目录','{}');
