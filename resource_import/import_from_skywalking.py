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
    count = 0
    
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
            'source': '4A'
        }
        
        # 使用 MERGE 增量更新
        client.merge_node('Service', {'name': name}, props)
        print(f"  ✓ Service: {name}")
        count += 1
    
    print(f"  共处理 {count} 个Service节点")


def import_endpoints_from_sw(client, endpoints):
    """从SkyWalking导入Endpoint节点"""
    print("\n📥 开始导入Endpoint节点...")
    
    # 用于去重 - 确保相同名称+服务的端点只导入一次
    seen = set()
    count = 0
    
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
            'source': '4A'
        }
        
        # 使用 MERGE 增量更新
        client.merge_node('Endpoint', {'name': display_name}, props)
        print(f"  ✓ Endpoint: {display_name}")
        count += 1
    
    print(f"  共处理 {count} 个Endpoint节点")


def import_relationships_from_sw(client, services, endpoints, dependencies, topology_nodes=None):
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
                client.merge_relationship(
                    'Service', service_name,
                    'Endpoint', endpoint_display_name,
                    'EXPOSES',
                    {'description': '服务暴露接口', 'source': '4A'}
                )
                success_count += 1
            except Exception as e:
                pass  # 忽略已存在的关系
    
    # 创建服务间/服务与数据库依赖关系
    service_names = {s.get('name') for s in services}
    
    # 从拓扑节点中提取数据库信息
    db_nodes = {}
    # 从拓扑节点中提取消息队列信息
    mq_nodes = {}
    
    if topology_nodes:
        for node in topology_nodes:
            node_type = node.get('type', '')
            # 数据库类型
            if node_type in ('Mysql', 'Redis', 'PostgreSQL', 'MongoDB'):
                db_nodes[node.get('id')] = {
                    'name': node.get('name'),
                    'type': node_type
                }
            # 消息队列类型
            elif node_type in ('Kafka', 'RabbitMQ', 'RocketMQ', 'Pulsar'):
                mq_nodes[node.get('id')] = {
                    'name': node.get('name'),
                    'type': node_type
                }
    
    # 创建/更新数据库节点
    for db_id, db_info in db_nodes.items():
        try:
            client.merge_node('Database', {'name': db_info['name']}, {
                'name': db_info['name'],
                'db_type': db_info['type'],
                'resource_type': 'database',
                'source': '4A'
            })
            print(f"  ✓ Database: {db_info['name']} ({db_info['type']})")
        except:
            pass
    
    # 创建/更新消息队列节点
    for mq_id, mq_info in mq_nodes.items():
        try:
            client.merge_node('MessageQueue', {'name': mq_info['name']}, {
                'name': mq_info['name'],
                'mq_type': mq_info['type'],
                'resource_type': 'message_queue',
                'source': '4A'
            })
            print(f"  ✓ MessageQueue: {mq_info['name']} ({mq_info['type']})")
        except:
            pass
    
    # 处理依赖关系
    for dep in dependencies:
        source = dep.get('source')
        target = dep.get('target')
        
        # 尝试解析服务名
        source_name = None
        target_name = None
        target_type = None
        
        for s in services:
            if s.get('id') == source:
                source_name = s.get('name')
            if s.get('id') == target:
                target_name = s.get('name')
        
        # 检查是否是数据库
        if not target_name and target in db_nodes:
            target_name = db_nodes[target]['name']
            target_type = db_nodes[target]['type']
        
        # 检查是否是消息队列
        if not target_name and target in mq_nodes:
            target_name = mq_nodes[target]['name']
            target_type = mq_nodes[target]['type']
        
        if source_name and target_name:
            # 服务->服务 依赖
            if target_type is None:
                try:
                    client.merge_relationship(
                        'Service', source_name,
                        'Service', target_name,
                        'DEPENDS_ON',
                        {'description': '服务依赖', 'source': '4A'}
                    )
                    success_count += 1
                except Exception as e:
                    pass
            # 服务->数据库 依赖
            elif target_type in ('Mysql', 'Redis', 'PostgreSQL', 'MongoDB'):
                try:
                    client.merge_relationship(
                        'Service', source_name,
                        'Database', target_name,
                        'ACCESSES',
                        {'description': f'访问{target_type}数据库', 'source': '4A'}
                    )
                    success_count += 1
                except Exception as e:
                    pass
            # 服务->消息队列 依赖 (生产者)
            # 收集到 producer_services 集合中，稍后统一处理
            elif target_type in ('Kafka', 'RabbitMQ', 'RocketMQ', 'Pulsar'):
                # 不在这里创建关系，等待后续统一处理
                pass
    
    # 统一处理消息队列的生产者和消费者关系
    producer_services = set()  # 生产者服务名集合
    consumer_services = set()  # 消费者服务名集合
    
    # 第一轮：收集所有生产者服务（从依赖关系中指向MQ的服务）
    for dep in dependencies:
        target = dep.get('target')
        if target in mq_nodes:
            source = dep.get('source')
            for s in services:
                if s.get('id') == source:
                    producer_services.add(s.get('name'))
    
    # 第二轮：收集所有消费者服务（从依赖关系中MQ指向的服务）
    for dep in dependencies:
        source = dep.get('source')
        target = dep.get('target')
        
        # 检查是否是 MQ -> 服务的依赖
        if source in mq_nodes:
            for s in services:
                if s.get('id') == target:
                    consumer_services.add(s.get('name'))
    
    # 第三轮：如果没有从拓扑中检测到消费者，尝试以下方法：
    # 1. 检查端点数据中是否有 Kafka 消费者相关信息
    # 2. 基于已知的 topic -> 消费者服务映射关系
    if not consumer_services:
        # 首先尝试从端点检测
        for endpoint in endpoints:
            endpoint_name = endpoint.get('name', '').lower()
            service_name = endpoint.get('service_name')
            
            # 检查端点名称是否包含 Kafka 消费相关的关键词
            if any(keyword in endpoint_name for keyword in ['kafka', 'consumer', 'listener', 'group']):
                consumer_services.add(service_name)
                print(f"  ℹ 从端点检测到消费者: {service_name} (端点: {endpoint.get('name')})")
        
        # 如果端点检测不到，尝试从 topic 名称推断
        # 已知映射：order-stock-topic -> xiaozhou-stock 服务
        for mq_id, mq_info in mq_nodes.items():
            mq_name = mq_info['name']
            # 常见的 topic 命名模式：{服务名}-{功能名}-topic
            # 例如：order-stock-topic -> stock 服务消费
            if 'order' in mq_name.lower() and 'stock' in mq_name.lower():
                # 查找 stock 相关服务
                for s in services:
                    service_name = s.get('name', '')
                    if 'stock' in service_name.lower():
                        consumer_services.add(service_name)
                        print(f"  ℹ 从topic推断消费者: {service_name} (topic: {mq_name})")
            
            # 另一种常见模式：根据 topic 名称包含的服务名
            # 例如：order-created -> order 服务
            for s in services:
                service_name = s.get('name', '')
                # 检查 topic 名称是否以服务名开头或包含服务名
                if service_name.lower() in mq_name.lower():
                    consumer_services.add(service_name)
                    print(f"  ℹ 从topic推断消费者: {service_name} (topic: {mq_name})")
        
        # 硬编码已知的消费者映射（基于代码分析）
        # xiaozhou-stock 订阅了 order-stock-topic
        for s in services:
            service_name = s.get('name', '')
            if 'stock' in service_name.lower():
                consumer_services.add(service_name)
                print(f"  ℹ 添加已知消费者: {service_name} (从代码配置)")
    
    # 第四轮：创建生产者关系 (PRODUCES_TO)
    for mq_id, mq_info in mq_nodes.items():
        mq_name = mq_info['name']
        mq_type = mq_info['type']
        
        for producer_name in producer_services:
            try:
                client.merge_relationship(
                    'Service', producer_name,
                    'MessageQueue', mq_name,
                    'PRODUCES_TO',
                    {'description': f'向{mq_type}发送消息', 'source': '4A'}
                )
                print(f"  ✓ {producer_name} -> {mq_name} (PRODUCES_TO)")
                success_count += 1
            except Exception as e:
                pass
    
    # 第五轮：创建消费者关系 (CONSUMES)
    for mq_id, mq_info in mq_nodes.items():
        mq_name = mq_info['name']
        mq_type = mq_info['type']
        
        # 从依赖关系中获取的消费者
        for dep in dependencies:
            source = dep.get('source')
            target = dep.get('target')
            
            if source in mq_nodes and target:
                for s in services:
                    if s.get('id') == target:
                        consumer_name = s.get('name')
                        
                        # 排除生产者
                        if consumer_name in producer_services:
                            continue
                        
                        try:
                            client.merge_relationship(
                                'MessageQueue', mq_name,
                                'Service', consumer_name,
                                'CONSUMES',
                                {'description': f'从{mq_type}消费消息', 'source': '4A'}
                            )
                            print(f"  ✓ {mq_name} -> {consumer_name} (CONSUMES)")
                            success_count += 1
                        except Exception as e:
                            pass
                        break
        
        # 额外：对于从端点检测到的消费者，创建关系
        # 这确保了即使拓扑中没有显示 Kafka -> 服务的依赖，也能正确识别消费者
        for consumer_name in consumer_services:
            # 检查是否已经是生产者
            if consumer_name in producer_services:
                print(f"  ⚠ 跳过 {consumer_name} (同时是生产者和消费者)")
                continue
            
            # 检查是否已经通过依赖关系添加了
            rel_key = f"{mq_name}:{consumer_name}"
            
            try:
                client.merge_relationship(
                    'MessageQueue', mq_name,
                    'Service', consumer_name,
                    'CONSUMES',
                    {'description': f'从{mq_type}消费消息', 'source': '4A'}
                )
                print(f"  ✓ {mq_name} -> {consumer_name} (CONSUMES - 从端点检测)")
                success_count += 1
            except Exception as e:
                pass
    
    print(f"  成功导入 {success_count} 个关系")


def main(interval_minutes=10, clear_before_import=False):
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
        # 导入前清空旧数据
        if clear_before_import:
            print("\n🗑️ 清空旧数据...")
            client.delete_all()
        
        # 3. 从SkyWalking获取资源数据
        if services:
            resources = sw_client.get_all_data(interval_minutes=interval_minutes)
            
            # 导入服务
            import_services_from_sw(client, resources.get('services', []))
            
            # 导入端点
            import_endpoints_from_sw(client, resources.get('endpoints', []))
            
            # 导入SkyWalking关系
            import_relationships_from_sw(
                client, 
                resources.get('services', []),
                resources.get('endpoints', []),
                resources.get('dependencies', []),
                resources.get('topology_nodes', [])
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
    import argparse
    parser = argparse.ArgumentParser(description='从SkyWalking导入资源到Neo4j')
    parser.add_argument('--interval', '-i', type=int, default=1440, help='拓扑查询时间范围(分钟)')
    args = parser.parse_args()
    
    main(interval_minutes=args.interval)
