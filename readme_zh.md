## Sumsg Smart

### 介绍

此自定义集成实现SUMSG平台智能产品接入 Home Assistant 平台。

### 支持

| 型号 | 产品名称 |
|----------------|-----------------------|
| pcSw1        | WiFi 开机卡1代           |
| pcS3         | WiFi 开机卡2代           |
| powerSwitch1 | 智能开关1代              |
| pcHealth1    | PC 硬件监控              |
| HA-WBC-2     | WiFi 开机卡局域网版2代    |

### 安装

手动安装:
把该库文件解压到 Home Assistant 的 `custom_components` 目录下。
如果不存在 `custom_components` 目录，请先创建。
目录结构如下:

```
-config
--custom_components
---sumsg_smart
```

### 配置

1. 重启 Home Assistant
2. 在添加集成中搜索 `Sumsg Smart`
3. 输入 [SUMSG平台账号和密码](https://app.sumsg.com)
