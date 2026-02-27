# -*- coding: utf-8 -*-
"""
SkyWalking客户端 - 从SkyWalking OAP动态获取资源信息
"""
import sys
import io

# 设置控制台输出编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

import requests
import json
import time
from config import SKYWALKING_OAP_URL, OPENSEARCH_URL, DOCKER_CONFIG


class SkyWalkingClient:
    def __init__(self, oap_url=None):
        """初始化SkyWalking客户端"""
        self.oap_url = (oap_url or SKYWALKING_OAP_URL).rstrip('/')
        self.graphql_url = f"{self.oap_url}/graphql"
        self.opensearch_url = OPENSEARCH_URL
        self.docker_url = DOCKER_CONFIG.get('url')
    
    def _get_timestamp_str(self, minutes=0):
        """获取时间戳字符串（毫秒）"""
        ts = int((time.time() * 1000)) - (minutes * 60 * 1000)
        return str(ts)
    
    def _get_datetime_str(self, minutes=0):
        """获取日期时间字符串，格式: YYYY-MM-DD HHmm"""
        now = time.time() - (minutes * 60)
        return time.strftime("%Y-%m-%d %H%M", time.localtime(now))
    
    def _query(self, query, variables=None):
        """执行GraphQL查询"""
        try:
            payload = {"query": query}
            if variables:
                payload["variables"] = variables
            
            response = requests.post(
                self.graphql_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"  ✗ HTTP {response.status_code}: {response.text[:200]}")
                return None
            
            result = response.json()
            
            # 如果有错误，打印出来
            if 'errors' in result:
                for err in result['errors']:
                    print(f"  ✗ GraphQL错误: {err.get('message', err)}")
            
            return result
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
        """获取服务的端点列表 - 使用 searchEndpoint API"""
        # searchEndpoint 不需要 duration 参数
        query = f"""
        {{
            searchEndpoint(serviceId: "{service_id}", keyword: "", limit: 100) {{
                id
                name
            }}
        }}
        """
        
        result = self._query(query)
        if result and 'data' in result:
            endpoints = result['data'].get('searchEndpoint', [])
            if endpoints:
                # 转换格式
                return [{'id': e.get('id'), 'name': e.get('name'), 'type': 'HTTP', 'serviceId': service_id} for e in endpoints]
        
        print(f"    ⚠ 无法获取端点数据")
        return []
    
    def get_service_dependencies(self, service_id, minutes=10):
        """获取服务的依赖关系"""
        # 使用最近几分钟的时间范围，与scheduler频率一致
        start_time = self._get_datetime_str(minutes=minutes)
        end_time = self._get_datetime_str()
        
        query = f"""
        {{
            getServiceTopology(serviceId: "{service_id}", duration: {{start: "{start_time}", end: "{end_time}", step: MINUTE}}) {{
                nodes {{
                    id
                    name
                    type
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
            nodes = topology.get('nodes', [])
            calls = topology.get('calls', [])
            print(f"    ✓ 获取到 {len(nodes)} 个节点, {len(calls)} 条调用")
            return nodes, calls
        
        print(f"    ⚠ 无法获取依赖关系")
        return [], []
    
    def get_service_instances(self, service_id, service_name, minutes=10):
        """从SkyWalking OAP获取服务实例"""
        start_time = self._get_datetime_str(minutes=minutes)
        end_time = self._get_datetime_str()
        
        query = f"""
        {{
            getServiceInstances(serviceId: "{service_id}", duration: {{start: "{start_time}", end: "{end_time}", step: MINUTE}}) {{
                id
                name
                attributes {{
                    name
                    value
                }}
            }}
        }}
        """
        
        result = self._query(query)
        instances = []
        if result and 'data' in result:
            data = result['data'].get('getServiceInstances', [])
            for inst in data:
                # 提取属性
                attrs = {}
                for attr in inst.get('attributes', []):
                    attrs[attr.get('name', '')] = attr.get('value', '')
                
                instance_data = {
                    'id': inst.get('id'),
                    'name': inst.get('name'),
                    'service_id': service_id,
                    'service_name': service_name,
                    'attributes': attrs,
                    'resource_type': 'service_instance'
                }
                instances.append(instance_data)
            
            if instances:
                print(f"    ✓ 从SkyWalking OAP获取到 {len(instances)} 个实例")
        
        return instances
    
    def get_instances_from_opensearch(self, service_names=None):
        """从OpenSearch获取服务实例信息（OTel指标）"""
        instances = []
        seen = set()
        
        try:
            # 首先尝试获取可用的metrics-otel索引列表
            import datetime
            today = datetime.date.today()
            
            # 尝试最近3天的索引
            index_patterns = []
            for i in range(3):
                date = today - datetime.timedelta(days=i)
                index_patterns.append(f"metrics-otel-{date.strftime('%Y.%m.%d')}")
            
            # 尝试查询每个索引
            for index_name in index_patterns:
                try:
                    # 先检查索引是否存在
                    check_url = f"{self.opensearch_url}/{index_name}"
                    check_response = requests.head(check_url, timeout=5)
                    if check_response.status_code != 200:
                        continue
                    
                    # 查询服务实例信息
                    query = {
                        "size": 0,
                        "aggs": {
                            "instances": {
                                "terms": {
                                    "field": "resource.attributes.service@instance@id",
                                    "size": 100
                                }
                            }
                        }
                    }
                    
                    url = f"{self.opensearch_url}/{index_name}/_search"
                    response = requests.post(url, json=query, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        buckets = data.get('aggregations', {}).get('instances', {}).get('buckets', [])
                        
                        for bucket in buckets:
                            instance_id = bucket.get('key')
                            if instance_id and instance_id not in seen:
                                seen.add(instance_id)
                                
                                # 解析服务名和实例名
                                parts = instance_id.split(':')
                                service_name = parts[0] if parts else ''
                                instance_name = instance_id
                                
                                # 如果指定了服务名过滤
                                if service_names and service_name not in service_names:
                                    continue
                                
                                instances.append({
                                    'id': instance_id,
                                    'name': instance_name,
                                    'service_name': service_name,
                                    'source': 'opensearch',
                                    'resource_type': 'service_instance'
                                })
                        
                        if instances:
                            print(f"    ✓ 从OpenSearch({index_name})获取到 {len(instances)} 个服务实例")
                            break
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"    ⚠ 从OpenSearch获取实例失败: {e}")
        
        return instances
    
    def get_containers_from_docker(self):
        """从Docker API获取容器信息"""
        containers = []
        
        try:
            # 首先尝试通过Dockerode库
            try:
                from docker import DockerClient
                client = DockerClient(base_url=self.docker_url)
                docker_containers = client.containers.list()
                
                for c in docker_containers:
                    container_data = {
                        'id': c.id[:12],
                        'name': c.name,
                        'image': c.image.tags[0] if c.image.tags else c.image.short_id,
                        'status': c.status,
                        'created': c.attrs.get('Created', ''),
                        'resource_type': 'container'
                    }
                    
                    # 获取端口映射
                    ports = []
                    for container_port, host_bindings in c.ports.items():
                        if host_bindings:
                            for binding in host_bindings:
                                ports.append(f"{binding['HostIp']}:{binding['HostPort']}->{container_port}")
                        else:
                            ports.append(container_port)
                    container_data['ports'] = ports
                    
                    # 获取标签（用于关联服务）
                    container_data['labels'] = c.labels
                    
                    containers.append(container_data)
                
                if containers:
                    print(f"    ✓ 从Docker API获取到 {len(containers)} 个容器")
                    
            except ImportError:
                # 如果没有docker库，使用HTTP API
                url = f"{self.docker_url}/containers/json"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    docker_containers = response.json()
                    
                    for c in docker_containers:
                        container_data = {
                            'id': c.get('Id', '')[:12],
                            'name': c.get('Names', [''])[0].lstrip('/'),
                            'image': c.get('Image', ''),
                            'status': c.get('State', ''),
                            'created': c.get('Created', 0),
                            'resource_type': 'container'
                        }
                        
                        # 获取端口映射
                        ports = []
                        for port, bindings in c.get('Ports', {}).items():
                            if bindings:
                                for binding in bindings:
                                    ports.append(f"{binding.get('HostIp', '')}:{binding.get('HostPort', '')}->{port}")
                            else:
                                ports.append(str(port))
                        container_data['ports'] = ports
                        
                        # 获取标签
                        container_data['labels'] = c.get('Labels', {})
                        
                        containers.append(container_data)
                    
                    if containers:
                        print(f"    ✓ 从Docker API获取到 {len(containers)} 个容器")
                        
        except Exception as e:
            print(f"    ⚠ 从Docker API获取容器失败: {e}")
        
        return containers
    
    def get_all_data(self, interval_minutes=10):
        """获取所有资源数据"""
        print("\n📥 开始从SkyWalking获取资源数据...")
        
        resources = {
            'services': [],
            'endpoints': [],
            'dependencies': [],
            'topology_nodes': [],
            'instances': [],
            'containers': []
        }
        
        # 收集所有拓扑节点（包含数据库等）
        all_topology_nodes = []
        
        # 1. 获取所有服务
        print("\n  🔍 获取服务列表...")
        services = self.get_services()
        service_names = set()
        
        for service in services:
            if not service.get('normal', True):
                continue  # 跳过已下线的服务
            
            service_name = service.get('name')
            service_names.add(service_name)
            
            service_data = {
                'id': service.get('id'),
                'name': service_name,
                'resource_type': 'microservice'
            }
            resources['services'].append(service_data)
            
            # 2. 获取每个服务的端点
            print(f"\n  🔍 获取服务 [{service_name}] 的端点...")
            endpoints = self.get_service_endpoints(service.get('id'))
            
            for endpoint in endpoints:
                endpoint_data = {
                    'id': endpoint.get('id'),
                    'name': endpoint.get('name'),
                    'type': endpoint.get('type', 'HTTP'),
                    'service_id': endpoint.get('serviceId'),
                    'service_name': service_name,
                    'resource_type': 'http'
                }
                resources['endpoints'].append(endpoint_data)
            
            # 3. 获取服务依赖关系
            print(f"\n  🔍 获取服务 [{service_name}] 的依赖...")
            nodes, calls = self.get_service_dependencies(service.get('id'), minutes=interval_minutes)
            
            # 收集拓扑节点
            for node in nodes:
                if node not in all_topology_nodes:
                    all_topology_nodes.append(node)
            
            for call in calls:
                dep_data = {
                    'source': call.get('source'),
                    'target': call.get('target'),
                    'call_id': call.get('id')
                }
                resources['dependencies'].append(dep_data)
        
        resources['topology_nodes'] = all_topology_nodes
        
        # 4. 从SkyWalking OAP获取服务实例
        print("\n  🔍 获取服务实例 (从SkyWalking OAP)...")
        for service in services:
            if not service.get('normal', True):
                continue
            
            service_id = service.get('id')
            service_name = service.get('name')
            instances = self.get_service_instances(service_id, service_name, minutes=interval_minutes)
            resources['instances'].extend(instances)
        
        # 5. 从OpenSearch获取服务实例（补充）
        print("\n  🔍 获取服务实例 (从OpenSearch)...")
        opensearch_instances = self.get_instances_from_opensearch(service_names)
        # 去重并合并
        existing_ids = {inst['id'] for inst in resources['instances']}
        for inst in opensearch_instances:
            if inst['id'] not in existing_ids:
                resources['instances'].append(inst)
        
        # 6. 从Docker API获取容器信息
        print("\n  🔍 获取容器信息 (从Docker API)...")
        containers = self.get_containers_from_docker()
        resources['containers'].extend(containers)
        
        print(f"\n  ✓ 总计获取 {len(resources['services'])} 个服务")
        print(f"  ✓ 总计获取 {len(resources['endpoints'])} 个端点")
        print(f"  ✓ 总计获取 {len(resources['dependencies'])} 个依赖关系")
        print(f"  ✓ 总计获取 {len(resources['instances'])} 个实例")
        print(f"  ✓ 总计获取 {len(resources['containers'])} 个容器")
        
        return resources


if __name__ == "__main__":
    # 测试连接
    client = SkyWalkingClient()
    resources = client.get_all_data()
    print("\n获取到的资源数据:")
    print(json.dumps(resources, indent=2, ensure_ascii=False))
