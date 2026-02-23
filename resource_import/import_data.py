# -*- coding: utf-8 -*-
"""
数据清洗脚本 - 将资源清单和关联关系导入Neo4j
"""

import sys
from neo4j_client import Neo4jClient
from config import RESOURCES, RELATIONSHIPS


def import_services(client):
    """导入Service节点"""
    print("\n📥 开始导入Service节点...")
    services = RESOURCES['services']
    
    for service in services:
        name = service['name']
        props = service['properties']
        props['resource_type'] = service['type']
        
        client.merge_node('Service', {'name': name}, props)
        print(f"  ✓ Service: {name}")
    
    print(f"  共导入 {len(services)} 个Service节点")


def import_endpoints(client):
    """导入Endpoint节点"""
    print("\n📥 开始导入Endpoint节点...")
    endpoints = RESOURCES['endpoints']
    
    for endpoint in endpoints:
        name = endpoint['name']
        props = endpoint['properties']
        props['resource_type'] = endpoint['type']
        
        client.merge_node('Endpoint', {'name': name}, props)
        print(f"  ✓ Endpoint: {name} ({props.get('method', 'N/A')})")
    
    print(f"  共导入 {len(endpoints)} 个Endpoint节点")


def import_databases(client):
    """导入Database节点"""
    print("\n📥 开始导入Database节点...")
    databases = RESOURCES['databases']
    
    for db in databases:
        name = db['name']
        props = db['properties']
        props['resource_type'] = db['type']
        
        client.merge_node('Database', {'name': name}, props)
        print(f"  ✓ Database: {name} ({props.get('host', 'N/A')}:{props.get('port', 'N/A')})")
    
    print(f"  共导入 {len(databases)} 个Database节点")


def import_kafkas(client):
    """导入Kafka节点"""
    print("\n📥 开始导入Kafka节点...")
    kafkas = RESOURCES['kafkas']
    
    for kafka in kafkas:
        name = kafka['name']
        props = kafka['properties']
        props['resource_type'] = kafka['type']
        
        client.merge_node('Kafka', {'name': name}, props)
        print(f"  ✓ Kafka: {name} ({props.get('host', 'N/A')}:{props.get('port', 'N/A')})")
    
    print(f"  共导入 {len(kafkas)} 个Kafka节点")


def import_containers(client):
    """导入Container节点"""
    print("\n📥 开始导入Container节点...")
    containers = RESOURCES['containers']
    
    for container in containers:
        name = container['name']
        props = container['properties']
        props['resource_type'] = container['type']
        
        client.merge_node('Container', {'name': name}, props)
        print(f"  ✓ Container: {name} ({props.get('image', 'N/A')})")
    
    print(f"  共导入 {len(containers)} 个Container节点")


def import_hosts(client):
    """导入Host节点"""
    print("\n📥 开始导入Host节点...")
    hosts = RESOURCES['hosts']
    
    for host in hosts:
        name = host['name']
        props = host['properties']
        props['resource_type'] = host['type']
        
        client.merge_node('Host', {'name': name}, props)
        print(f"  ✓ Host: {name} ({props.get('type', 'N/A')})")
    
    print(f"  共导入 {len(hosts)} 个Host节点")


def import_relationships(client):
    """导入关联关系"""
    print("\n🔗 开始导入关联关系...")
    
    success_count = 0
    fail_count = 0
    
    for rel in RELATIONSHIPS:
        from_type = rel['from_type']
        from_name = rel['from_name']
        to_type = rel['to_type']
        to_name = rel['to_name']
        rel_type = rel['relation']
        description = rel.get('description', '')
        
        try:
            client.create_relationship(
                from_type, from_name,
                to_type, to_name,
                rel_type,
                {'description': description}
            )
            print(f"  ✓ {from_type}:{from_name} --[{rel_type}]--> {to_type}:{to_name}")
            success_count += 1
        except Exception as e:
            print(f"  ✗ 关系创建失败: {from_type}:{from_name} --[{rel_type}]--> {to_type}:{to_name}")
            print(f"    错误: {e}")
            fail_count += 1
    
    print(f"\n  成功导入: {success_count} 个关系")
    if fail_count > 0:
        print(f"  导入失败: {fail_count} 个关系")


def print_resource_summary():
    """打印资源清单摘要"""
    print("\n" + "="*60)
    print("📋 资源清单摘要")
    print("="*60)
    
    total_resources = 0
    for category, items in RESOURCES.items():
        count = len(items)
        total_resources += count
        print(f"  {category}: {count}")
    
    print(f"\n  资源总计: {total_resources}")
    print(f"  关联关系: {len(RELATIONSHIPS)}")
    print("="*60)


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 资源数据清洗工具 - 导入到Neo4j")
    print("="*60)
    
    # 打印资源清单摘要
    print_resource_summary()
    
    # 连接Neo4j
    client = Neo4jClient()
    
    if not client.connect():
        print("\n❌ 无法连接到Neo4j，请检查配置")
        sys.exit(1)
    
    try:
        # 清空现有数据（可选）
        # print("\n🗑️ 清空现有数据...")
        # client.delete_all()
        
        # 导入所有节点
        print("\n" + "-"*60)
        print("📦 开始导入节点")
        print("-"*60)
        
        import_services(client)
        import_endpoints(client)
        import_databases(client)
        import_kafkas(client)
        import_containers(client)
        import_hosts(client)
        
        # 导入关系
        print("\n" + "-"*60)
        print("🔗 开始导入关系")
        print("-"*60)
        
        import_relationships(client)
        
        # 打印结果摘要
        client.print_summary()
        
        print("\n✅ 数据导入完成！")
        
    except Exception as e:
        print(f"\n❌ 导入过程中发生错误: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
