# -*- coding: utf-8 -*-
"""
动态数据清洗脚本 - 从SkyWalking获取资源并导入Neo4j
"""
import sys
import json
import io

# 设置控制台输出编码（仅在未设置时）
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

from neo4j_client import Neo4jClient
from skywalking_client import SkyWalkingClient


def import_services_from_sw(client, services):
    """从SkyWalking导入Service节点"""
    print("\n📥 开始导入Service节点...")
    
    for service in services:
        name = service.get('name', 'unknown')
        props = {
            'name': name,
            'id': service.get('id', ''),
            'layer': service.get('layer', ''),
            'resource_type': 'microservice',
            'create_user': 'system',
            'source': 'skywalking'
        }
        
        client.merge_node('Service', {'name': name}, props)
        print(f"  ✓ Service: {name}")
    
    print(f"  共导入 {len(services)} 个Service节点")


def import_endpoints_from_sw(client, endpoints):
    """从SkyWalking导入Endpoint节点"""
    print("\n📥 开始导入Endpoint节点...")
    
    for endpoint in endpoints:
        name = endpoint.get('name', 'unknown')
        props = {
            'name': name,
            'id': endpoint.get('id', ''),
            'type': endpoint.get('type', 'HTTP'),
            'service_name': endpoint.get('service_name', ''),
            'resource_type': 'http',
            'create_user': 'system',
            'source': 'skywalking'
        }
        
        client.merge_node('Endpoint', {'name': name}, props)
        print(f"  ✓ Endpoint: {name}")
    
    print(f"  共导入 {len(endpoints)} 个Endpoint节点")


def import_relationships_from_sw(client, services, endpoints, dependencies):
    """从SkyWalking导入关联关系"""
    print("\n🔗 开始导入关联关系...")
    
    # 建立服务与端点的关联
    success_count = 0
    
    # 创建服务-端点关系
    for endpoint in endpoints:
        service_name = endpoint.get('service_name')
        if service_name:
            try:
                client.create_relationship(
                    'Service', service_name,
                    'Endpoint', endpoint.get('name'),
                    'EXPOSES',
                    {'description': '服务暴露接口', 'source': 'skywalking'}
                )
                success_count += 1
            except Exception as e:
                pass  # 忽略已存在的关系
    
    # 创建服务间依赖关系
    service_names = {s.get('name') for s in services}
    
    for dep in dependencies:
        source = dep.get('source')
        target = dep.get('target')
        
        # 尝试解析服务名
        source_name = None
        target_name = None
        
        for s in services:
            if s.get('id') == source:
                source_name = s.get('name')
            if s.get('id') == target:
                target_name = s.get('name')
        
        if source_name and target_name:
            try:
                client.create_relationship(
                    'Service', source_name,
                    'Service', target_name,
                    'DEPENDS_ON',
                    {'description': '服务依赖', 'source': 'skywalking'}
                )
                success_count += 1
            except Exception as e:
                pass  # 忽略已存在的关系
    
    print(f"  成功导入 {success_count} 个关系")


def get_additional_resources():
    """
    获取额外的资源信息（数据库、Kafka等）
    这些信息需要从其他数据源获取，或者从SkyWalking的Service Instance中推断
    """
    print("\n📥 获取额外资源信息...")
    
    resources = {
        'services': [],
        'endpoints': [],
        'databases': [],
        'kafkas': [],
        'containers': [],
        'hosts': []
    }
    
    # 这里可以添加从其他数据源获取资源的逻辑
    # 例如：
    # 1. 从Kubernetes API获取容器信息
    # 2. 从Prometheus获取数据库监控信息
    # 3. 从Docker API获取容器列表
    # 4. 从Nacos获取服务元数据
    
    # 暂时返回预配置的静态数据作为补充
    from config import RESOURCES
    
    if 'services' in RESOURCES:
        resources['services'] = RESOURCES['services']
    
    if 'endpoints' in RESOURCES:
        resources['endpoints'] = RESOURCES['endpoints']
    
    if 'databases' in RESOURCES:
        resources['databases'] = RESOURCES['databases']
    
    if 'kafkas' in RESOURCES:
        resources['kafkas'] = RESOURCES['kafkas']
    
    if 'containers' in RESOURCES:
        resources['containers'] = RESOURCES['containers']
    
    if 'hosts' in RESOURCES:
        resources['hosts'] = RESOURCES['hosts']
    
    return resources


def import_additional_resources(client, resources):
    """导入额外资源（数据库、Kafka等）"""
    
    # 导入服务
    if 'services' in resources and resources['services']:
        print("\n📥 导入Service节点...")
        for svc in resources['services']:
            name = svc.get('name')
            props = svc.get('properties', {})
            props['resource_type'] = svc.get('type', 'microservice')
            props['source'] = 'config'
            
            client.merge_node('Service', {'name': name}, props)
            print(f"  ✓ Service: {name}")
    
    # 导入端点
    if 'endpoints' in resources and resources['endpoints']:
        print("\n📥 导入Endpoint节点...")
        for ep in resources['endpoints']:
            name = ep.get('name')
            props = ep.get('properties', {})
            props['resource_type'] = ep.get('type', 'http')
            props['source'] = 'config'
            
            client.merge_node('Endpoint', {'name': name}, props)
            print(f"  ✓ Endpoint: {name}")
    
    # 导入数据库
    if 'databases' in resources and resources['databases']:
        print("\n📥 导入Database节点...")
        for db in resources['databases']:
            name = db.get('name')
            props = db.get('properties', {})
            props['resource_type'] = db.get('type', 'mysql')
            props['source'] = 'config'
            
            client.merge_node('Database', {'name': name}, props)
            print(f"  ✓ Database: {name}")
    
    # 导入Kafka
    if 'kafkas' in resources and resources['kafkas']:
        print("\n📥 导入Kafka节点...")
        for kafka in resources['kafkas']:
            name = kafka.get('name')
            props = kafka.get('properties', {})
            props['resource_type'] = kafka.get('type', 'mq')
            props['source'] = 'config'
            
            client.merge_node('Kafka', {'name': name}, props)
            print(f"  ✓ Kafka: {name}")
    
    # 导入容器
    if 'containers' in resources and resources['containers']:
        print("\n📥 导入Container节点...")
        for container in resources['containers']:
            name = container.get('name')
            props = container.get('properties', {})
            props['resource_type'] = container.get('type', 'docker')
            props['source'] = 'config'
            
            client.merge_node('Container', {'name': name}, props)
            print(f"  ✓ Container: {name}")
    
    # 导入主机
    if 'hosts' in resources and resources['hosts']:
        print("\n📥 导入Host节点...")
        for host in resources['hosts']:
            name = host.get('name')
            props = host.get('properties', {})
            props['resource_type'] = host.get('type', 'host')
            props['source'] = 'config'
            
            client.merge_node('Host', {'name': name}, props)
            print(f"  ✓ Host: {name}")


def import_static_relationships(client):
    """导入静态配置的关联关系"""
    print("\n🔗 导入静态关联关系...")
    
    from config import RELATIONSHIPS
    
    success_count = 0
    fail_count = 0
    for rel in RELATIONSHIPS:
        try:
            client.create_relationship(
                rel['from_type'], rel['from_name'],
                rel['to_type'], rel['to_name'],
                rel['relation'],
                {'description': rel.get('description', ''), 'source': 'config'}
            )
            print(f"  OK: {rel['from_type']}:{rel['from_name']} --[{rel['relation']}]--> {rel['to_type']}:{rel['to_name']}")
            success_count += 1
        except Exception as e:
            print(f"  FAIL: {rel['from_type']}:{rel['from_name']} --[{rel['relation']}]--> {rel['to_type']}:{rel['to_name']} - {e}")
            fail_count += 1
    
    print(f"  成功导入 {success_count} 个关系, 失败 {fail_count} 个")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 动态资源数据清洗工具 - 从SkyWalking获取并导入Neo4j")
    print("="*60)
    
    # 1. 连接SkyWalking
    print("\n📡 连接SkyWalking OAP...")
    sw_client = SkyWalkingClient()  # 使用config.py中的localhost配置
    
    # 测试连接
    services = sw_client.get_services()
    if not services:
        print("\n⚠️ 无法连接到SkyWalking或获取数据为空")
        print("   将仅导入静态配置的资源...")
    
    # 2. 连接Neo4j
    client = Neo4jClient()
    
    if not client.connect():
        print("\n❌ 无法连接到Neo4j，请检查配置")
        sys.exit(1)
    
    try:
        # 3. 从SkyWalking获取资源数据
        if services:
            resources = sw_client.get_all_data()
            
            # 导入服务
            import_services_from_sw(client, resources.get('services', []))
            
            # 导入端点
            import_endpoints_from_sw(client, resources.get('endpoints', []))
            
            # 导入SkyWalking关系
            import_relationships_from_sw(
                client, 
                resources.get('services', []),
                resources.get('endpoints', []),
                resources.get('dependencies', [])
            )
        
        # 4. 获取并导入额外资源（数据库、Kafka等）
        additional_resources = get_additional_resources()
        import_additional_resources(client, additional_resources)
        
        # 5. 导入静态配置的关系
        import_static_relationships(client)
        
        # 6. 打印结果摘要
        client.print_summary()
        
        print("\n✅ 数据导入完成！")
        print("\n💡 说明:")
        print("   - 服务和端点数据来自SkyWalking OAP")
        print("   - 数据库、Kafka、容器等配置来自静态config.py")
        print("   - 关系数据综合了动态和静态来源")
        
    except Exception as e:
        print(f"\n❌ 导入过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
