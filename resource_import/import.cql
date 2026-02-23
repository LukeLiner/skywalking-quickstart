// Neo4j数据导入Cypher脚本
// 资源节点创建

// 1. 创建Service节点
CREATE (s1:Service {name: 'xiaozhou-product', resource_type: 'microservice', port: '8090', service: 'xiaozhou-product', create_user: 'lindiqi'})
CREATE (s2:Service {name: 'xiaozhou-order', resource_type: 'microservice', port: '8090', service: 'xiaozhou-order', create_user: 'lindiqi'})

// 2. 创建Endpoint节点
CREATE (e1:Endpoint {name: '/product/page', resource_type: 'http', method: 'GET', service: 'xiaozhou-product', create_user: 'lindiqi'})
CREATE (e2:Endpoint {name: '/product/{id}', resource_type: 'http', method: 'GET', service: 'xiaozhou-product', create_user: 'lindiqi'})
CREATE (e3:Endpoint {name: '/order/getOrder', resource_type: 'http', method: 'POST', service: 'xiaozhou-order', create_user: 'lindiqi'})

// 3. 创建Database节点
CREATE (d1:Database {name: 'mytestshop', resource_type: 'mysql', host: 'mysql-db', port: '3306', create_user: 'lindiqi'})

// 4. 创建Kafka节点
CREATE (k1:Kafka {name: 'Kafka', resource_type: 'mq', host: 'kafka', port: '9092', create_user: 'lindiqi'})

// 5. 创建Container节点
CREATE (c1:Container {name: 'xiaozhou-product-001', resource_type: 'docker', image: 'xiaozhou-product:latest', container_id: 'container_xxxxx_1', name: 'xiaozhou_product', pod_name: 'pod_xxxx_1', create_user: 'lindiqi'})
CREATE (c2:Container {name: 'xiaozhou-order-001', resource_type: 'docker', image: 'xiaozhou-order:latest', container_id: 'container_xxxxx_2', name: 'xiaozhou_order', pod_name: 'pod_xxxx_2', create_user: 'lindiqi'})

// 6. 创建Host节点
CREATE (h1:Host {name: '172.20.0.x', resource_type: 'host', type: 'docker-bridge', create_user: 'lindiqi'})

// 7. 创建关联关系

// Container CONTAINS Service (容器部署服务)
CREATE (c1)-[:CONTAINS {description: '容器部署服务'}]->(s1)
CREATE (c2)-[:CONTAINS {description: '容器部署服务'}]->(s2)

// Host RUNS_ON Container (主机运行容器)
CREATE (h1)-[:RUNS_ON {description: '主机运行容器'}]->(c1)
CREATE (h1)-[:RUNS_ON {description: '主机运行容器'}]->(c2)

// Service EXPOSES Endpoint (服务暴露接口)
CREATE (s1)-[:EXPOSES {description: '服务暴露接口'}]->(e1)
CREATE (s1)-[:EXPOSES {description: '服务暴露接口'}]->(e2)
CREATE (s2)-[:EXPOSES {description: '服务暴露接口'}]->(e3)

// Service ACCESSES Database (服务访问数据库)
CREATE (s1)-[:ACCESSES {description: '服务访问数据库'}]->(d1)
CREATE (s2)-[:ACCESSES {description: '服务访问数据库'}]->(d1)

// Service USES Kafka (服务使用消息队列)
CREATE (s1)-[:USES {description: '服务使用消息队列'}]->(k1)
CREATE (s2)-[:USES {description: '服务使用消息队列'}]->(k1)

RETURN '数据导入完成'
