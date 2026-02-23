# Neo4j连接配置
# Docker环境：使用容器名连接
# 本地测试：使用 localhost:7687
NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',  # Windows本地连接Docker容器
    'user': 'neo4j',
    'password': 'neo4j123'
}

# SkyWalking OAP连接配置
SKYWALKING_OAP_URL = 'http://localhost:12800'
