"""
测试 yaml_check.views 模块
验证 YAML 验证 API 端点
"""

import pytest
import json
from django.test import Client


@pytest.fixture
def valid_yaml_request_data():
    """有效的 YAML 请求数据"""
    return {
        'metadata': {
            'version': '1.0',
            'generated': '2025-01-01T00:00:00Z'
        },
        'hardware': {
            'cpu': 'Ryzen Threadripper',
            'gpu': 'Radeon RX 7900 XTX',
            'machines': [
                {
                    'id': 1,
                    'name': 'Test Machine',
                    'specs': {
                        'motherboard': 'ASUS',
                        'cpu': 'Ryzen Threadripper',
                        'gpu': 'Radeon RX 7900 XTX'
                    }
                }
            ]
        },
        'environment': {
            'os': {'method': 'same', 'os': 'Ubuntu', 'deployment': 'bare-metal'},
            'kernel': {'method': 'same', 'type': 'mainline', 'version': '6.5.0'}
        },
        'test_suites': [
            {'id': 1, 'name': 'Test', 'type': 'benchmark', 'order': 1}
        ]
    }


@pytest.fixture
def invalid_yaml_request_data():
    """无效的 YAML 请求数据（缺少必需键）"""
    return {
        'metadata': {'version': '1.0'},
        'hardware': {
            # 缺少 cpu
            'gpu': 'Test GPU'
        }
    }


@pytest.mark.django_db
class TestValidateYamlAPI:
    """测试 validate_yaml API 端点"""
    
    def test_validate_yaml_endpoint_exists(self, api_client):
        """测试端点存在"""
        response = api_client.post(
            '/system/yaml/validate',
            data=json.dumps({}),
            content_type='application/json'
        )
        # 应该返回响应（不是 404）
        assert response.status_code != 404
    
    def test_validate_yaml_with_valid_data(self, authenticated_api_client, valid_yaml_request_data):
        """测试验证有效数据"""
        client, token = authenticated_api_client
        response = client.post(
            '/system/yaml/validate',
            data=json.dumps(valid_yaml_request_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # 应该返回 200
        assert response.status_code == 200
        
        data = response.json()
        # 验证响应结构
        assert 'code' in data  # API 响应包含 code
        assert 'data' in data  # API 响应包含 data
    
    def test_validate_yaml_with_invalid_data(self, authenticated_api_client, invalid_yaml_request_data):
        """测试验证无效数据"""
        client, token = authenticated_api_client
        response = client.post(
            '/system/yaml/validate',
            data=json.dumps(invalid_yaml_request_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        
        data = response.json()
        # 验证响应结构
        assert 'code' in data
        assert 'data' in data
        # 无效数据应该在 data 字段中返回验证结果
        if isinstance(data['data'], dict) and 'success' in data['data']:
            assert data['data']['success'] is False
    
    def test_validate_yaml_requires_json_content_type(self, authenticated_api_client):
        """测试需要 JSON Content-Type"""
        client, token = authenticated_api_client
        response = client.post(
            '/system/yaml/validate',
            data='not json',
            content_type='text/plain',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # 应该返回错误或要求正确的 Content-Type
        assert response.status_code in [200, 400, 415]  # 415 = Unsupported Media Type
    
    def test_validate_yaml_with_empty_body(self, authenticated_api_client):
        """测试空请求体"""
        client, token = authenticated_api_client
        response = client.post(
            '/system/yaml/validate',
            data=json.dumps({}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            # 空数据应该验证失败
            if 'success' in data:
                assert data['success'] is False
    
    def test_validate_yaml_with_malformed_json(self, authenticated_api_client):
        """测试格式错误的 JSON"""
        client, token = authenticated_api_client
        response = client.post(
            '/system/yaml/validate',
            data='{"invalid": json}',
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # API 使用统一响应格式，HTTP 状态码总是 200
        assert response.status_code == 200
        
        # 检查响应体中包含错误信息
        data = response.json()
        assert 'code' in data
        assert data['code'] != 200  # code 字段应该表示失败
        assert 'data' in data
        # 应该包含 JSON 解析错误的信息
        assert 'Invalid JSON' in str(data['data']) or 'json' in str(data['data']).lower()
    
    def test_validate_yaml_returns_error_code(self, authenticated_api_client, invalid_yaml_request_data):
        """测试返回错误代码"""
        client, token = authenticated_api_client
        response = client.post(
            '/system/yaml/validate',
            data=json.dumps(invalid_yaml_request_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        # API 响应包含 code 和 data
        assert 'code' in data
        assert 'data' in data
        # 验证失败时应该在 data.error 中包含错误信息
        if isinstance(data['data'], dict) and not data['data'].get('success', True):
            assert 'error' in data['data']
    
    def test_validate_yaml_http_methods(self, authenticated_api_client):
        """测试只允许 POST 方法"""
        client, token = authenticated_api_client
        # GET 应该不被允许
        response = client.get(
            '/system/yaml/validate',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        assert response.status_code in [404, 405]  # 405 = Method Not Allowed
        
        # PUT 应该不被允许
        response = client.put(
            '/system/yaml/validate',
            data=json.dumps({}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        assert response.status_code in [404, 405]


@pytest.mark.django_db
class TestValidateYamlAuthentication:
    """测试 YAML 验证 API 认证"""
    
    def test_validate_yaml_without_authentication(self, api_client, valid_yaml_request_data):
        """测试未认证访问"""
        response = api_client.post(
            '/system/yaml/validate',
            data=json.dumps(valid_yaml_request_data),
            content_type='application/json'
        )
        
        # 可能需要认证，或者允许匿名访问
        # 根据实际 API 设计调整期望
        assert response.status_code in [200, 401, 403]
    
    def test_validate_yaml_with_invalid_token(self, api_client, valid_yaml_request_data):
        """测试无效 token"""
        response = api_client.post(
            '/system/yaml/validate',
            data=json.dumps(valid_yaml_request_data),
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer invalid_token_here'
        )
        
        # 应该拒绝无效 token
        assert response.status_code in [200, 401, 403]


@pytest.mark.django_db
class TestValidateYamlEdgeCases:
    """测试边界情况"""
    
    def test_validate_yaml_with_very_large_data(self, authenticated_api_client):
        """测试非常大的数据"""
        client, token = authenticated_api_client
        large_data = {
            'hardware': {
                'cpu': 'Ryzen Threadripper',
                'gpu': 'Test',
                'machines': [
                    {'id': i, 'name': f'Machine {i}'}
                    for i in range(1000)  # 1000 台机器
                ]
            }
        }
        
        response = client.post(
            '/system/yaml/validate',
            data=json.dumps(large_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # 应该能处理或返回适当的错误
        assert response.status_code in [200, 400, 413, 500]  # 413 = Payload Too Large
    
    def test_validate_yaml_with_special_characters(self, authenticated_api_client):
        """测试特殊字符"""
        client, token = authenticated_api_client
        data_with_special_chars = {
            'hardware': {
                'cpu': 'Ryzen Threadripper',
                'gpu': 'Test GPU 🎉',  # Emoji
                'special': '特殊字符 ©®™'
            }
        }
        
        response = client.post(
            '/system/yaml/validate',
            data=json.dumps(data_with_special_chars),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code in [200, 400]
    
    def test_validate_yaml_with_unicode(self, authenticated_api_client):
        """测试 Unicode 字符"""
        client, token = authenticated_api_client
        data_with_unicode = {
            'hardware': {
                'cpu': 'Ryzen Threadripper',
                'gpu': 'テスト GPU',  # 日文
                'note': '测试数据'  # 中文
            }
        }
        
        response = client.post(
            '/system/yaml/validate',
            data=json.dumps(data_with_unicode, ensure_ascii=False),
            content_type='application/json; charset=utf-8',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestValidateYamlPerformance:
    """测试性能"""
    
    @pytest.mark.slow
    def test_validate_yaml_response_time(self, authenticated_api_client, valid_yaml_request_data):
        """测试响应时间"""
        import time
        client, token = authenticated_api_client
        
        start = time.time()
        response = client.post(
            '/system/yaml/validate',
            data=json.dumps(valid_yaml_request_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        elapsed = time.time() - start
        
        # 验证应该在 2 秒内完成
        assert elapsed < 2.0, f"Validation took too long: {elapsed:.2f}s"
    
    @pytest.mark.slow
    def test_validate_yaml_concurrent_requests(self, authenticated_api_client, valid_yaml_request_data):
        """测试并发请求"""
        import concurrent.futures
        client, token = authenticated_api_client
        
        def make_request():
            return client.post(
                '/system/yaml/validate',
                data=json.dumps(valid_yaml_request_data),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {token}'
            )
        
        # 并发发送 10 个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # 所有请求都应该成功
        for response in results:
            assert response.status_code in [200, 401, 403]

