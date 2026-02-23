# -*- coding: utf-8 -*-
"""
SkyWalking客户端 - 从SkyWalking OAP动态获取资源信息
使用正确的GraphQL查询格式
"""

import requests
import json
import time
from config import SKYWALKING_OAP_URL


class SkyWalkingClient:
    def __init__(self, oap_url=None):
        """初始化SkyWalking客户端"""
        self.oap_url = (oap_url or SKYWALKING_OAP_URL).rstrip('/')
        self.graphql_url = f"{self.oap_url}/graphql"
    
    def _get_timestamp_str(self, minutes=0):
        """获取时间戳字符串（毫秒）"""
        ts = int((time.time() * 1000)) - (minutes * 60 * 1000)
        return str(ts)
    
    def _query(self, query):
        """执行GraphQL查询（使用内联变量）"""
        try:
            response = requests.post(
                self.graphql_url,
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  ✗ GraphQL查询失败: {e}")
            return None
    
    def get_services(self):
        """获取所有服务列表"""
        start_time = self._get_timestamp_str(minutes=5)
        end_time = self._get_timestamp_str()
        
        query = f"""
        {{
            services: getAllServices(duration: {{start: "{start_time}", end: "{end_time}", step: MINUTE}}) {{
                id
                name
                normal
            }}
        }}
        """
        
        result = self._query(query)
        if result and 'data' in result:
            services = result['data'].get('services', [])
            print(f"  ✓ 获取到 {len(services)} 个服务")
            return services
        
        print("  ✗ 获取服务列表失败")
        return []
    
    def get_service_endpoints(self, service_id):
        """获取服务的端点列表"""
        start_time = self._get_timestamp_str(minutes=5)
        end_time = self._get_timestamp_str()
        
        # 转义service_id中的特殊字符
        escaped_id = service_id.replace('"', '\\"')
        
        query = f"""
        {{
            getServiceEndpoints(serviceId: "{escaped_id}", duration: {{start: "{start_time}", end: "{end_time}", step: MINUTE}}) {{
                id
                name
                type
                serviceId
            }}
        }}
        """
        
        result = self._query(query)
        if result and 'data' in result:
            endpoints = result['data'].get('getServiceEndpoints', [])
            return endpoints
        
        return []
    
    def get_service_dependencies(self, service_id):
        """获取服务的依赖关系（从拓扑中获取）"""
        start_time = self._get_timestamp_str(minutes=5)
        end_time = self._get_timestamp_str()
        
        escaped_id = service_id.replace('"', '\\"')
        
        query = f"""
        {{
            getServiceTopology(serviceId: "{escaped_id}", duration: {{start: "{start_time}", end: "{end_time}", step: MINUTE}}) {{
                nodes {{
                    id
                    name
                    type
                    serviceId
                }}
                calls {{
                    source
                    target
                    id
                }}
            }}
        }}
        """
        
        result = self._query(query)
        if result and 'data' in result:
            topology = result['data'].get('getServiceTopology', {})
            return topology.get('nodes', []), topology.get('calls', [])
        
        return [], []
    
    def get_all_service_instances(self, service_id):
        """获取服务的实例列表"""
        start_time = self._get_timestamp_str(minutes=5)
        end_time = self._get_timestamp_str()
        
        escaped_id = service_id.replace('"', '\\"')
        
        query = f"""
        {{
            getServiceInstances(serviceId: "{escaped_id}", duration: {{start: "{start_time}", end: "{end_time}", step: MINUTE}}) {{
                id
                name
                serviceId
                instanceId
            }}
        }}
        """
        
        result = self._query(query)
        if result and 'data' in result:
            instances = result['data'].get('getServiceInstances', [])
            return instances
        
        return []
    
    def get_all_data(self):
        """获取所有资源数据"""
        print("\n📥 开始从SkyWalking获取资源数据...")
        
        resources = {
            'services': [],
            'endpoints': [],
            'dependencies': []
        }
        
        # 1. 获取所有服务
        print("\n  🔍 获取服务列表...")
        services = self.get_services()
        
        for service in services:
            if not service.get('normal', True):
                continue  # 跳过已下线的服务
            
            service_data = {
                'id': service.get('id'),
                'name': service.get('name'),
                'resource_type': 'microservice'
            }
            resources['services'].append(service_data)
            
            # 2. 获取每个服务的端点
            print(f"\n  🔍 获取服务 [{service.get('name')}] 的端点...")
            endpoints = self.get_service_endpoints(service.get('id'))
            
            for endpoint in endpoints:
                endpoint_data = {
                    'id': endpoint.get('id'),
                    'name': endpoint.get('name'),
                    'type': endpoint.get('type', 'HTTP'),
                    'service_id': endpoint.get('serviceId'),
                    'service_name': service.get('name'),
                    'resource_type': 'http'
                }
                resources['endpoints'].append(endpoint_data)
            
            # 3. 获取服务依赖关系
            print(f"\n  🔍 获取服务 [{service.get('name')}] 的依赖...")
            nodes, calls = self.get_service_dependencies(service.get('id'))
            
            for call in calls:
                dep_data = {
                    'source': call.get('source'),
                    'target': call.get('target'),
                    'call_id': call.get('id')
                }
                resources['dependencies'].append(dep_data)
        
        print(f"\n  ✓ 总计获取 {len(resources['services'])} 个服务")
        print(f"  ✓ 总计获取 {len(resources['endpoints'])} 个端点")
        print(f"  ✓ 总计获取 {len(resources['dependencies'])} 个依赖关系")
        
        return resources


if __name__ == "__main__":
    # 测试连接
    client = SkyWalkingClient()
    resources = client.get_all_data()
    print("\n获取到的资源数据:")
    print(json.dumps(resources, indent=2, ensure_ascii=False))
