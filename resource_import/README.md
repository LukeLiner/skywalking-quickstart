# 资源数据清洗工具

将资源清单和关联关系导入到Neo4j图数据库。

## 功能特性

### 两种数据获取方式

1. **动态获取** - 从SkyWalking OAP实时获取服务和端点数据
2. **静态配置** - 从config.py读取数据库、Kafka、容器等配置

### 数据源

| 数据类型 | 获取方式 | 说明 |
|---------|---------|------|
| Service | SkyWalking OAP | 动态获取 |
| Endpoint | SkyWalking OAP | 动态获取 |
| Database | 静态配置 | config.py |
| Kafka | 静态配置 | config.py |
| Container | 静态配置 | config.py |
| Host | 静态配置 | config.py |

## 资源清单（示例配置）

本工具实现了以下资源类型的导入：

### 节点类型

| 类型 | 数量 | 描述 |
|------|------|------|
| Service | 动态 | 微服务（从SkyWalking获取） |
| Endpoint | 动态 | HTTP接口（从SkyWalking获取） |
| Database | 1 | MySQL数据库 |
| Kafka | 1 | 消息队列 |
| Container | 2 | Docker容器 |
| Host | 1 | 主机 |

### 资源详情

#### Service (微服务)
- `xiaozhou-product` - 产品服务 (port:8090)
- `xiaozhou-order` - 订单服务 (port:8090)

#### Endpoint (HTTP接口)
- `/product/page` - 产品分页接口 (GET, 属于xiaozhou-product)
- `/product/{id}` - 产品详情接口 (GET, 属于xiaozhou-product)
- `/order/getOrder` - 订单查询接口 (POST, 属于xiaozhou-order)

#### Database (数据库)
- `mytestshop` - MySQL数据库 (host:mysql-db, port:3306)

#### Kafka (消息队列)
- `Kafka` - Kafka消息队列 (host:kafka, port:9092)

#### Container (容器)
- `xiaozhou-product-001` - 产品服务容器 (image:xiaozhou-product:latest)
- `xiaozhou-order-001` - 订单服务容器 (image:xiaozhou-order:latest)

#### Host (主机)
- `172.20.0.x` - Docker桥接网络主机

## 关联关系

| 源节点 | 关系类型 | 目标节点 | 描述 |
|--------|----------|----------|------|
| Container | CONTAINS | Service | 容器部署服务 |
| Host | RUNS_ON | Container | 主机运行容器 |
| Service | EXPOSES | Endpoint | 服务暴露接口 |
| Service | ACCESSES | Database | 服务访问数据库 |
| Service | USES | Kafka | 服务使用消息队列 |

## 关系图

```
                    ┌─────────────┐
                    │     Host    │
                    │ 172.20.0.x │
                    └──────┬──────┘
                           │ RUNS_ON
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
     │ Container   │ │ Container │ │   (other)   │
     │xiaozhou-    │ │xiaozhou-  │ │   nodes     │
     │product-001 │ │order-001  │ └─────────────┘
     └──────┬──────┘ └─────┬─────┘
            │ CONTAINS     │ CONTAINS
     ┌──────▼──────┐ ┌─────▼─────┐
     │  Service    │ │ Service   │
     │xiaozhou-    │ │xiaozhou-  │
     │ product     │ │ order     │
     └──────┬──────┘ └─────┬─────┘
            │              │
     ┌─────┼─────┐  ┌─────┼─────┐
     │     │     │  │     │     │
     ▼     ▼     ▼  ▼     ▼     ▼
  ┌─────┬─────┬───────┬─────┐
  │Endpoint    │Database│Kafka│
  │/product/...│mytestshop│Kafka │
  └─────────────┴───────┴─────┘
```

## 安装

### 方式一：Docker Compose 启动 Neo4j

在项目根目录运行：
```bash
docker-compose up -d neo4j
```

Neo4j 服务信息：
- HTTP端口: http://localhost:7474
- Bolt端口: localhost:7687
- 用户名: neo4j
- 密码: neo4j123

### 方式二：使用Python脚本导入

1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 配置Neo4j连接（编辑`config.py`）：
```python
# Docker容器内连接
NEO4J_CONFIG = {
    'uri': 'bolt://neo4j:7687',
    'user': 'neo4j',
    'password': 'neo4j123'
}

# 本地调试时使用
# NEO4J_CONFIG = {
#     'uri': 'bolt://localhost:7687',
#     'user': 'neo4j',
#     'password': 'neo4j123'
# }
```

## 使用

### 方式一：动态导入（推荐）- 从SkyWalking获取
从SkyWalking OAP动态获取服务、端点数据，并结合静态配置导入：
```bash
python import_from_skywalking.py
```

此方式会：
1. 连接SkyWalking OAP获取所有服务列表
2. 获取每个服务的端点信息
3. 从拓扑中获取服务间依赖关系
4. 导入数据库、Kafka等静态配置的资源
5. 建立所有关联关系并存储到Neo4j

### 方式二：定时自动同步
启动定时任务，自动从SkyWalking获取数据并导入Neo4j：
```bash
python scheduler.py           # 默认5分钟执行一次
python scheduler.py 1        # 每1分钟执行一次（测试用）
python scheduler.py 10       # 每10分钟执行一次
```

### 方式二：静态导入 - 使用预配置数据
使用config.py中预定义的资源清单导入：
```bash
python import_data.py
```

### 方式三：使用Cypher脚本导入
1. 访问 Neo4j Browser: http://localhost:7474
2. 登录 (neo4j/neo4j123)
3. 点击数据库图标，选择导入按钮
4. 上传 `import.cql` 文件执行

## 动态获取的数据流程

```
┌─────────────────┐     GraphQL      ┌─────────────────┐
│  SkyWalking     │ ──────────────→  │  Python Client  │
│  OAP Server     │ ←────────────── │                 │
│  (Port 12800)   │   JSON Response │  skywalking_     │
└─────────────────┘                  │  client.py      │
                                      └────────┬────────┘
                                               │
                                               ▼
┌─────────────────┐     Cypher       ┌─────────────────┐
│    Neo4j        │ ←────────────── │  Data Importer  │
│  (Port 7687)    │ ──────────────→ │                 │
│                 │   CREATE Nodes   │ import_from_    │
└─────────────────┘                  │ skywalking.py   │
                                      └─────────────────┘
```

### 扩展数据源

如需从其他数据源动态获取资源，可以扩展以下模块：
- **Kubernetes**: 从K8s API获取容器、Pod、Service信息
- **Prometheus**: 获取监控指标中的数据库、Kafka等服务
- **Docker**: 从Docker API获取容器列表
- **Nacos**: 从Nacos获取服务注册信息

## 输出示例

```
============================================================
🚀 资源数据清洗工具 - 导入到Neo4j
============================================================

============================================================
📋 资源清单摘要
============================================================
  services: 2
  endpoints: 3
  databases: 1
  kafkas: 1
  containers: 2
  hosts: 1

  资源总计: 10
  关联关系: 11
============================================================

------------------------------------------------------------
📦 开始导入节点
------------------------------------------------------------

📥 开始导入Service节点...
  ✓ Service: xiaozhou-product
  ✓ Service: xiaozhou-order
  共导入 2 个Service节点

📥 开始导入Endpoint节点...
  ✓ Endpoint: /product/page (GET)
  ✓ Endpoint: /product/{id} (GET)
  ✓ Endpoint: /order/getOrder (POST)
  共导入 3 个Endpoint节点

...

============================================================
📊 Neo4j数据库摘要
============================================================
  节点总数: 10
  关系总数: 11
============================================================

📦 节点类型分布:
  - Service: 2
  - Endpoint: 3
  - Database: 1
  - Kafka: 1
  - Container: 2
  - Host: 1

🔗 关系类型分布:
  - CONTAINS: 2
  - RUNS_ON: 2
  - EXPOSES: 3
  - ACCESSES: 2
  - USES: 2

✅ 数据导入完成！
```

## Neo4j Browser查询示例

查看所有节点：
```cypher
MATCH (n) RETURN n
```

查看服务及其关联：
```cypher
MATCH (s:Service)-[r]->(n) RETURN s.name, type(r), n
```

查看完整的资源拓扑：
```cypher
MATCH p=()-[r]->() RETURN p
```
