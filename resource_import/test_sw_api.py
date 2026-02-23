# -*- coding: utf-8 -*-
"""
SkyWalking API Test Tool
Run: python test_sw_api.py
"""

import requests
import json
import time
import sys
import io

# Set UTF-8 encoding for output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SKYWALKING_OAP_URL = 'http://localhost:12800'
GRAPHQL_URL = f"{SKYWALKING_OAP_URL}/graphql"

def get_timestamp_ms(minutes=5):
    """Get timestamp in milliseconds"""
    ts = int((time.time() * 1000)) - (minutes * 60 * 1000)
    return str(ts)

def test_graphql(query, variables=None):
    """Test GraphQL query"""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(
        GRAPHQL_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    print(f"HTTP Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Response: {response.text[:500]}")
        return None
    
    result = response.json()
    
    if 'errors' in result:
        print("GraphQL Errors:")
        for err in result['errors']:
            print(f"  - {err.get('message', err)}")
        return None
    
    return result

def test_services():
    """Test getting services"""
    print("\n" + "="*50)
    print("Test 1: Get All Services")
    print("="*50)
    
    start_time = get_timestamp_ms(minutes=5)
    end_time = get_timestamp_ms()
    
    print(f"Using timestamp: {start_time} - {end_time}")
    
    query = f"""
    {{
        services: getAllServices(duration: {{start: "{start_time}", end: "{end_time}", step: MINUTE}}) {{
            id
            name
            normal
        }}
    }}
    """
    
    result = test_graphql(query)
    if result and 'data' in result:
        services = result['data'].get('services', [])
        print(f"OK: Got {len(services)} services:")
        for s in services:
            print(f"  - {s.get('name')} (id: {s.get('id')})")
        return services
    return []

def test_endpoints(service_id, service_name):
    """Test getting endpoints"""
    print("\n" + "="*50)
    print(f"Test 2: Get Endpoints for [{service_name}]")
    print("="*50)
    
    # searchEndpoint works!
    query = f"""
    {{
        searchEndpoint(serviceId: "{service_id}", keyword: "", limit: 100) {{
            id
            name
        }}
    }}
    """
    
    print(f"\nTrying API: searchEndpoint")
    result = test_graphql(query)
    if result and 'data' in result:
        endpoints = result['data'].get('searchEndpoint', [])
        if endpoints:
            print(f"OK: Got {len(endpoints)} endpoints:")
            for e in endpoints:
                print(f"  - {e.get('name')}")
            return endpoints
        else:
            print(f"Empty list returned")
    
    print("FAIL: Endpoint API failed")
    return []

def test_topology(service_id, service_name):
    """Test getting topology"""
    print("\n" + "="*50)
    print(f"Test 3: Get Topology for [{service_name}]")
    print("="*50)
    
    start_time = get_timestamp_ms(minutes=5)
    end_time = get_timestamp_ms()
    
    print(f"Using timestamp: {start_time} - {end_time}")
    
    # Try with String variables instead of Long
    query = """
    query GetTopology($serviceId: ID!, $start: String!, $end: String!) {
        getServiceTopology(serviceId: $serviceId, duration: {start: $start, end: $end, step: MINUTE}) {
            nodes {
                id
                name
                type
            }
            calls {
                source
                target
            }
        }
    }
    """
    
    variables = {
        'serviceId': service_id,
        'start': start_time,
        'end': end_time
    }
    
    print(f"\nTrying: getServiceTopology with String variables")
    result = test_graphql(query, variables)
    if result and 'data' in result:
        topology = result['data'].get('getServiceTopology', {})
        if topology:
            nodes = topology.get('nodes', [])
            calls = topology.get('calls', [])
            print(f"  Nodes: {len(nodes)}, Edges: {len(calls)}")
            if nodes:
                print(f"  Node names: {[n.get('name') for n in nodes]}")
            if calls:
                print(f"  Calls: {calls}")
            return nodes, calls
        else:
            print(f"  Empty topology")
    else:
        print(f"  Failed")
    
    print("FAIL: Topology API failed")
    return [], []

def main():
    print("""
============================================================
SkyWalking API Test Tool
============================================================
""")
    
    # Test services
    services = test_services()
    
    if not services:
        print("\nCannot get services, test terminated")
        return
    
    # Select a service to test
    for service in services:
        if service.get('normal', True):
            service_id = service.get('id')
            service_name = service.get('name')
            break
    
    # Test endpoints
    test_endpoints(service_id, service_name)
    
    # Test topology
    test_topology(service_id, service_name)
    
    print("\n" + "="*50)
    print("Test Complete")
    print("="*50)

if __name__ == "__main__":
    main()
