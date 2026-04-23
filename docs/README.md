# 文档索引

本目录包含 **Automatic Email Responder** 的运维、开发与合规说明。日常请从下列入口阅读；项目分阶段实施记录已移至 `[archive/](archive/)`，避免与现行手册混在一起。

**若只需一份文档了解「当前实现了什么」**：请读 **[已实现功能说明.md](已实现功能说明.md)**（功能总览，中文）。

## 按角色


| 角色          | 建议阅读                                                                                                                                                                           |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **产品 / 管理** | **[已实现功能说明.md](已实现功能说明.md)**                                                                                                                                        |
| **开发**      | [已实现功能说明.md](已实现功能说明.md)、[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)、[ARCHITECTURE.md](ARCHITECTURE.md)、[CONFIGURATION.md](CONFIGURATION.md)、[TESTING.md](TESTING.md)、[API_REFERENCE.md](API_REFERENCE.md) |
| **运维**      | [已实现功能说明.md](已实现功能说明.md)、[OPERATOR_MANUAL.md](OPERATOR_MANUAL.md)、[DEPLOYMENT.md](DEPLOYMENT.md)、[CONFIGURATION.md](CONFIGURATION.md)                                                                   |
| **合规 / 隐私** | [已实现功能说明.md](已实现功能说明.md)、[PRIVACY_POLICY.md](PRIVACY_POLICY.md)                                                                                                                                         |


## 核心手册（顶层）


| 文档                                       | 说明                             |
| ---------------------------------------- | ------------------------------ |
| [已实现功能说明.md](已实现功能说明.md)           | **一体化功能总览**（当前实现边界）            |
| [ARCHITECTURE.md](ARCHITECTURE.md)       | 系统架构与组件                        |
| [API_REFERENCE.md](API_REFERENCE.md)     | HTTP API 说明                    |
| [CONFIGURATION.md](CONFIGURATION.md)     | 环境变量与 `backend/config/` 下 YAML |
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | 仓库结构、扩展类别与服务                   |
| [TESTING.md](TESTING.md)                 | 测试依赖与运行方式                      |
| [OPERATOR_MANUAL.md](OPERATOR_MANUAL.md) | 操作手册                           |
| [DEPLOYMENT.md](DEPLOYMENT.md)           | 部署说明                           |
| [PRIVACY_POLICY.md](PRIVACY_POLICY.md)   | 隐私政策文档                         |


## 历史与里程碑

分阶段总结、最终报告与校准报告已归档，便于审计与追溯，**不作为日常配置依据**：

- 总览：[archive/FINAL_REPORT.md](archive/FINAL_REPORT.md)
- 各阶段：`archive/PHASE*_SUMMARY.md`（含 `PHASE2.2_SUMMARY.md`）
- 置信度校准：[archive/CALIBRATION_REPORT.md](archive/CALIBRATION_REPORT.md)

> 若书签仍指向旧的 `docs/PHASE*.md` 或 `docs/FINAL_REPORT.md`，请改为上述 `archive/` 路径。

