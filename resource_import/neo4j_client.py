# -*- coding: utf-8 -*-
"""
Neo4j客户端 - 负责连接Neo4j数据库并执行Cypher查询
"""

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


if __name__ == "__main__":
    # 测试连接
    client = Neo4jClient()
    if client.connect():
        client.print_summary()
        client.close()
