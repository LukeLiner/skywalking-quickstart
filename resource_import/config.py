# Neo4j连接配置
# Docker环境：使用容器名连接
# 本地测试：使用 localhost:7687
NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',  # Windows本地连接Docker容器
    'user': 'neo4j',
    'password': 'neo4j123'
}

# SkyWalking OAP连接配置
SKYWALKING_OAP_URL = 'http://localhost:12800'  # Windows本地连接

# 本地调试时改为以下配置：
# NEO4J_CONFIG = {
#     'uri': 'bolt://localhost:7687',
#     'user': 'neo4j',
#     'password': 'neo4j123'
# }

# 资源清单配置
RESOURCES = {
    # Service资源
    'services': [
        {
            'name': 'xiaozhou-product',
            'type': 'microservice',
            'properties': {
                'port': '8090',
                'service': 'xiaozhou-product',
                'create_user': 'lindiqi'
            }
        },
        {
            'name': 'xiaozhou-order',
            'type': 'microservice',
            'properties': {
                'port': '8090',
                'service': 'xiaozhou-order',
                'create_user': 'lindiqi'
            }
        }
    ],
    
    # Endpoint资源
    'endpoints': [
        {
            'name': '/product/page',
            'type': 'http',
            'properties': {
                'method': 'GET',
                'service': 'xiaozhou-product',
                'create_user': 'lindiqi'
            }
        },
        {
            'name': '/product/{id}',
            'type': 'http',
            'properties': {
                'method': 'GET',
                'service': 'xiaozhou-product',
                'create_user': 'lindiqi'
            }
        },
        {
            'name': '/order/getOrder',
            'type': 'http',
            'properties': {
                'method': 'POST',
                'service': 'xiaozhou-order',
                'create_user': 'lindiqi'
            }
        }
    ],
    
    # Database资源
    'databases': [
        {
            'name': 'mytestshop',
            'type': 'mysql',
            'properties': {
                'host': 'mysql-db',
                'port': '3306',
                'create_user': 'lindiqi'
            }
        }
    ],
    
    # Kafka资源
    'kafkas': [
        {
            'name': 'Kafka',
            'type': 'mq',
            'properties': {
                'host': 'kafka',
                'port': '9092',
                'create_user': 'lindiqi'
            }
        }
    ],
    
    # Container资源
    'containers': [
        {
            'name': 'xiaozhou-product-001',
            'type': 'docker',
            'properties': {
                'image': 'xiaozhou-product:latest',
                'container_id': 'container_xxxxx_1',
                'container_name': 'xiaozhou_product',
                'pod_name': 'pod_xxxx_1',
                'create_user': 'lindiqi'
            }
        },
        {
            'name': 'xiaozhou-order-001',
            'type': 'docker',
            'properties': {
                'image': 'xiaozhou-order:latest',
                'container_id': 'container_xxxxx_2',
                'container_name': 'xiaozhou_order',
                'pod_name': 'pod_xxxx_2',
                'create_user': 'lindiqi'
            }
        }
    ],
    
    # Host资源
    'hosts': [
        {
            'name': '172.20.0.x',
            'type': 'host',
            'properties': {
                'type': 'docker-bridge',
                'create_user': 'lindiqi'
            }
        }
    ]
}

# 关联关系定义
RELATIONSHIPS = [
    # Container 部署 Service (CONTAINS)
    {
        'from_type': 'Container',
        'from_name': 'xiaozhou-product-001',
        'to_type': 'Service',
        'to_name': 'xiaozhou-product',
        'relation': 'CONTAINS',
        'description': '容器部署服务'
    },
    {
        'from_type': 'Container',
        'from_name': 'xiaozhou-order-001',
        'to_type': 'Service',
        'to_name': 'xiaozhou-order',
        'relation': 'CONTAINS',
        'description': '容器部署服务'
    },
    
    # Host 运行 Container (RUNS_ON)
    {
        'from_type': 'Host',
        'from_name': '172.20.0.x',
        'to_type': 'Container',
        'to_name': 'xiaozhou-product-001',
        'relation': 'RUNS_ON',
        'description': '主机运行容器'
    },
    {
        'from_type': 'Host',
        'from_name': '172.20.0.x',
        'to_type': 'Container',
        'to_name': 'xiaozhou-order-001',
        'relation': 'RUNS_ON',
        'description': '主机运行容器'
    },
    
    # Service 暴露 Endpoint (EXPOSES)
    {
        'from_type': 'Service',
        'from_name': 'xiaozhou-product',
        'to_type': 'Endpoint',
        'to_name': '/product/page',
        'relation': 'EXPOSES',
        'description': '服务暴露接口'
    },
    {
        'from_type': 'Service',
        'from_name': 'xiaozhou-product',
        'to_type': 'Endpoint',
        'to_name': '/product/{id}',
        'relation': 'EXPOSES',
        'description': '服务暴露接口'
    },
    {
        'from_type': 'Service',
        'from_name': 'xiaozhou-order',
        'to_type': 'Endpoint',
        'to_name': '/order/getOrder',
        'relation': 'EXPOSES',
        'description': '服务暴露接口'
    },
    
    # Service 访问 Database (ACCESSES)
    {
        'from_type': 'Service',
        'from_name': 'xiaozhou-product',
        'to_type': 'Database',
        'to_name': 'mytestshop',
        'relation': 'ACCESSES',
        'description': '服务访问数据库'
    },
    {
        'from_type': 'Service',
        'from_name': 'xiaozhou-order',
        'to_type': 'Database',
        'to_name': 'mytestshop',
        'relation': 'ACCESSES',
        'description': '服务访问数据库'
    },
    
    # Service 使用 Kafka (USES)
    {
        'from_type': 'Service',
        'from_name': 'xiaozhou-product',
        'to_type': 'Kafka',
        'to_name': 'Kafka',
        'relation': 'USES',
        'description': '服务使用消息队列'
    },
    {
        'from_type': 'Service',
        'from_name': 'xiaozhou-order',
        'to_type': 'Kafka',
        'to_name': 'Kafka',
        'relation': 'USES',
        'description': '服务使用消息队列'
    }
]
