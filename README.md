# 阅读打卡网站
安装依赖，运行app.py，并且需要打开该ip5001端口
changeDb用于修改用户权限，delete和lookfor用于后台查看修改数据库。
注册部分的学院选择，数据来源燕山大学
用户权限分为用户和管理员。用户只能查看当前时间段所属打卡记录和打卡总数。
管理员可以修改密码，设置时间段，查看用户除密码外信息，包括打卡详情。

## 技术运用
后端Flask，前端部分采用后端渲染。
数据库使用sqlite。
