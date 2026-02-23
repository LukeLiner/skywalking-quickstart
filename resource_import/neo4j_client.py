# -*- coding: utf-8 -*-
"""
Neo4j客户端 - 负责连接Neo4j数据库并执行Cypher查询
"""
import sys
import io

# 设置控制台输出编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

from neo4j import GraphDatabase
from config import NEO4J_CONFIG


class Neo4jClient:
    def __init__(self, uri=None, user=None, password=None):
        """初始化Neo4j客户端"""
        self.uri = uri or NEO4J_CONFIG['uri']
        self.user = user or NEO4J_CONFIG['user']
        self.password = password or NEO4J_CONFIG['password']
        self.driver = None
    
    def connect(self):
        """建立与Neo4j的连接"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # 验证连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            print(f"✓ 成功连接到Neo4j: {self.uri}")
            return True
        except Exception as e:
            print(f"✗ 连接Neo4j失败: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            print("✓ 已关闭Neo4j连接")
    
    def execute(self, query, parameters=None):
        """执行Cypher查询"""
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return list(result)
    
    def execute_single(self, query, parameters=None):
        """执行单条查询并返回单个结果"""
        with self.driver.session() as session:
            result = session.run(query, parameters)
            record = result.single()
            return record
    
    def create_node(self, label, properties):
        """创建节点"""
        # 清理属性键中的特殊字符
        clean_props = {k: v for k, v in properties.items() if v is not None}
        
        prop_str = ", ".join([f"{k}: ${k}" for k in clean_props.keys()])
        query = f"CREATE (n:{label} {{{prop_str}}}) RETURN n"
        
        result = self.execute(query, clean_props)
        return result
    
    def merge_node(self, label, match_props, properties):
        """合并节点（存在则更新，不存在则创建）"""
        # 清理属性
        clean_match = {k: v for k, v in match_props.items() if v is not None}
        clean_props = {k: v for k, v in properties.items() if v is not None}
        
        # 合并所有属性
        all_props = {**clean_match, **clean_props}
        
        # 构建MERGE的ON CREATE SET和ON MATCH SET子句
        set_clauses = []
        for key in all_props.keys():
            set_clauses.append(f"n.{key} = ${key}")
        
        prop_str = ", ".join(set_clauses)
        
        # 构建匹配条件
        match_parts = []
        for key in clean_match.keys():
            match_parts.append(f"n.{key} = ${key}")
        
        if match_parts:
            query = f"""
            MERGE (n:{label})
            ON CREATE SET {prop_str}
            ON MATCH SET {prop_str}
            RETURN n
            """
        else:
            query = f"""
            CREATE (n:{label})
            SET {prop_str}
            RETURN n
            """
        
        result = self.execute(query, all_props)
        return result
    
    def create_relationship(self, from_label, from_name, to_label, to_name, 
                           rel_type, rel_properties=None):
        """创建关系"""
        rel_props = rel_properties or {}
        clean_props = {k: v for k, v in rel_props.items() if v is not None}
        
        # 构建关系属性
        if clean_props:
            rel_prop_str = ", ".join([f"r.{k} = ${k}" for k in clean_props.keys()])
            query = f"""
            MATCH (from:{from_label})
            WHERE from.name = $from_name
            MATCH (to:{to_label})
            WHERE to.name = $to_name
            CREATE (from)-[r:{rel_type}]->(to)
            SET {rel_prop_str}
            RETURN r
            """
        else:
            query = f"""
            MATCH (from:{from_label})
            WHERE from.name = $from_name
            MATCH (to:{to_label})
            WHERE to.name = $to_name
            CREATE (from)-[r:{rel_type}]->(to)
            RETURN r
            """
        
        params = {
            'from_name': from_name,
            'to_name': to_name,
            **clean_props
        }
        
        result = self.execute(query, params)
        return result
    
    def delete_all(self):
        """删除所有节点和关系（清空数据库）"""
        query = "MATCH (n) DETACH DELETE n"
        self.execute(query)
        print("✓ 已清空所有节点和关系")
    
    def get_node_count(self):
        """获取节点数量"""
        query = "MATCH (n) RETURN count(n) as count"
        result = self.execute_single(query)
        return result['count'] if result else 0
    
    def get_relationship_count(self):
        """获取关系数量"""
        query = "MATCH ()-[r]->() RETURN count(r) as count"
        result = self.execute_single(query)
        return result['count'] if result else 0
    
    def get_all_nodes(self):
        """获取所有节点"""
        query = "MATCH (n) RETURN labels(n)[0] as type, n.name as name, n"
        results = self.execute(query)
        nodes = []
        for record in results:
            nodes.append({
                'type': record['type'],
                'name': record['name'],
                'properties': dict(record['n'])
            })
        return nodes
    
    def get_all_relationships(self):
        """获取所有关系"""
        query = """
        MATCH (from)-[r]->(to)
        RETURN labels(from)[0] as from_type, from.name as from_name,
               type(r) as relation, labels(to)[0] as to_type, to.name as to_name
        """
        results = self.execute(query)
        rels = []
        for record in results:
            rels.append({
                'from_type': record['from_type'],
                'from_name': record['from_name'],
                'relation': record['relation'],
                'to_type': record['to_type'],
                'to_name': record['to_name']
            })
        return rels
    
    def print_summary(self):
        """打印数据库摘要"""
        node_count = self.get_node_count()
        rel_count = self.get_relationship_count()
        
        print("\n" + "="*50)
        print("📊 Neo4j数据库摘要")
        print("="*50)
        print(f"  节点总数: {node_count}")
        print(f"  关系总数: {rel_count}")
        print("="*50 + "\n")
        
        # 按类型统计节点
        query = "MATCH (n) RETURN labels(n)[0] as type, count(n) as count ORDER BY count DESC"
        results = self.execute(query)
        
        print("📦 节点类型分布:")
        for record in results:
            print(f"  - {record['type']}: {record['count']}")
        
        # 按类型统计关系
        query = "MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY count DESC"
        results = self.execute(query)
        
        print("\n🔗 关系类型分布:")
        for record in results:
            print(f"  - {record['type']}: {record['count']}")
        
        print()


def clear_all_data(force=False):
    """清空Neo4j中所有数据"""
    client = Neo4jClient()
    if not client.connect():
        print("\nFailed to connect to Neo4j")
        return
    
    # 显示当前数据
    client.print_summary()
    
    if not force:
        print("\nWARNING: This will delete all nodes and relationships!")
        confirm = input("\nConfirm clear all data? (yes/no): ")
        if confirm.lower() != 'yes':
            print("\nCancelled")
            client.close()
            return
    
    client.delete_all()
    print("\nAll data cleared!")
    client.print_summary()
    client.close()


def query_nodes(label=None, name_pattern=None):
    """查询节点"""
    client = Neo4jClient()
    if not client.connect():
        return
    
    try:
        if label and name_pattern:
            query = f"MATCH (n:{label}) WHERE n.name CONTAINS $name RETURN n ORDER BY n.name"
            results = client.execute(query, {'name': name_pattern})
        elif label:
            query = f"MATCH (n:{label}) RETURN n ORDER BY n.name"
            results = client.execute(query)
        else:
            query = "MATCH (n) RETURN labels(n)[0] as type, n.name as name ORDER BY type, name"
            results = client.execute(query)
        
        print("\n" + "="*50)
        print("查询结果")
        print("="*50)
        
        if not results:
            print("无结果")
        else:
            for record in results:
                if label:
                    node = record['n']
                    print(f"  - {dict(node)}")
                else:
                    print(f"  - {record['type']}: {record['name']}")
        
        print()
    finally:
        client.close()


def query_relationships(rel_type=None, from_node=None, to_node=None):
    """查询关系"""
    client = Neo4jClient()
    if not client.connect():
        return
    
    try:
        conditions = []
        params = {}
        
        if rel_type:
            conditions.append(f"type(r) = '${rel_type}'")
        if from_node:
            conditions.append(f"from.name = $from_name")
            params['from_name'] = from_node
        if to_node:
            conditions.append(f"to.name = $to_name")
            params['to_name'] = to_node
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
        MATCH (from)-[r]->(to)
        WHERE {where_clause}
        RETURN from.name as from_name, type(r) as type, to.name as to_name
        ORDER BY from_name, type
        """
        
        results = client.execute(query, params)
        
        print("\n" + "="*50)
        print("关系查询结果")
        print("="*50)
        
        if not results:
            print("无结果")
        else:
            for record in results:
                print(f"  {record['from_name']} --[{record['type']}]--> {record['to_name']}")
        
        print()
    finally:
        client.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Neo4j数据库工具')
    parser.add_argument('--clear', action='store_true', help='清空所有数据')
    parser.add_argument('--force', '-f', action='store_true', help='强制执行不清空确认')
    parser.add_argument('--query', '-q', metavar='LABEL', help='查询指定类型的节点')
    parser.add_argument('--rels', '-r', metavar='TYPE', help='查询指定类型的关系')
    parser.add_argument('--all', '-a', action='store_true', help='显示所有数据')
    parser.add_argument('--search', '-s', metavar='NAME', help='按名称搜索节点')
    
    args = parser.parse_args()
    
    if args.clear:
        clear_all_data(force=args.force)
    elif args.all:
        client = Neo4jClient()
        if client.connect():
            print("\n=== 所有节点 ===")
            nodes = client.get_all_nodes()
            for n in nodes:
                print(f"  [{n['type']}] {n['name']}")
            
            print("\n=== 所有关系 ===")
            rels = client.get_all_relationships()
            for r in rels:
                print(f"  {r['from_name']} --[{r['relation']}]--> {r['to_name']}")
            
            client.print_summary()
            client.close()
    elif args.query:
        query_nodes(label=args.query)
    elif args.search:
        query_nodes(name_pattern=args.search)
    elif args.rels:
        query_relationships(rel_type=args.rels)
    else:
        # 测试连接
        client = Neo4jClient()
        if client.connect():
            client.print_summary()
            client.close()
        
        print("""
使用方法:
  python neo4j_client.py --all          # 查看所有数据
  python neo4j_client.py -q Service    # 查询所有Service节点
  python neo4j_client.py -q Endpoint    # 查询所有Endpoint节点
  python neo4j_client.py -r EXPOSES    # 查询所有EXPOSES关系
  python neo4j_client.py -s product     # 搜索名称包含product的节点
  python neo4j_client.py --clear         # 清空所有数据
""")
