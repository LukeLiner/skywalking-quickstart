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
    
    # 用于去重
    seen = set()
    
    for service in services:
        name = service.get('name', 'unknown')
        
        if name in seen:
            continue
        seen.add(name)
        
        props = {
            'name': name,
            'id': service.get('id', ''),
            'layer': service.get('layer', ''),
            'resource_type': 'microservice',
            'create_user': 'system',
            'source': 'skywalking'
        }
        
        # 使用 CREATE 确保每个服务都创建
        client.create_node('Service', props)
        print(f"  ✓ Service: {name}")
    
    print(f"  共导入 {len(seen)} 个Service节点")


def import_endpoints_from_sw(client, endpoints):
    """从SkyWalking导入Endpoint节点"""
    print("\n📥 开始导入Endpoint节点...")
    
    # 用于去重 - 确保相同名称+服务的端点只导入一次
    seen = set()
    
    for endpoint in endpoints:
        service_name = endpoint.get('service_name', '')
        name = endpoint.get('name', 'unknown')
        
        # 创建唯一标识: service_name + endpoint_name
        unique_key = f"{service_name}:{name}"
        if unique_key in seen:
            continue
        seen.add(unique_key)
        
        # 端点名称加上服务名前缀以确保唯一性
        display_name = f"{service_name}:{name}"
        
        props = {
            'name': display_name,
            'id': endpoint.get('id', ''),
            'type': endpoint.get('type', 'HTTP'),
            'service_name': service_name,
            'endpoint_name': name,
            'resource_type': 'http',
            'create_user': 'system',
            'source': 'skywalking'
        }
        
        # 使用 CREATE 而不是 MERGE
        client.create_node('Endpoint', props)
        print(f"  ✓ Endpoint: {display_name}")
    
    print(f"  共导入 {len(seen)} 个Endpoint节点")


def import_relationships_from_sw(client, services, endpoints, dependencies):
    """从SkyWalking导入关联关系"""
    print("\n🔗 开始导入关联关系...")
    
    # 建立服务与端点的关联
    success_count = 0
    
    # 创建服务-端点关系 (使用带服务前缀的名称)
    seen_rels = set()
    for endpoint in endpoints:
        service_name = endpoint.get('service_name')
        endpoint_name = endpoint.get('name', 'unknown')
        
        if service_name:
            # 使用带前缀的名称
            endpoint_display_name = f"{service_name}:{endpoint_name}"
            
            # 去重
            rel_key = f"{service_name}:{endpoint_display_name}"
            if rel_key in seen_rels:
                continue
            seen_rels.add(rel_key)
            
            try:
                client.create_relationship(
                    'Service', service_name,
                    'Endpoint', endpoint_display_name,
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
        print("   请检查SkyWalking OAP服务是否正常运行")
    
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
        else:
            print("\n⚠️ 未获取到SkyWalking数据，请检查OAP服务连接")
        
        # 4. 打印结果摘要
        client.print_summary()
        
        print("\n✅ 数据导入完成！")
        print("\n💡 说明:")
        print("   - 所有数据均来自SkyWalking OAP动态获取")
        
    except Exception as e:
        print(f"\n❌ 导入过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
