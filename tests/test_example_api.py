"""
示例 API 测试用例
展示如何使用 pytest 编写 Django API 测试
"""

import pytest
import json
from django.urls import reverse


# ==================== 单元测试示例 ====================

@pytest.mark.unit
def test_simple_assertion():
    """
    简单的断言测试
    """
    assert 1 + 1 == 2
    assert "hello".upper() == "HELLO"


# ==================== API 测试示例 ====================

@pytest.mark.api
@pytest.mark.django_db
class TestAuthAPI:
    """
    认证 API 测试类
    """
    
    def test_login_success(self, api_client, test_user):
        """
        测试成功登录
        """
        from base64 import b64encode
        
        # 准备登录数据
        password = 'testpass123'
        encoded_password = b64encode(password.encode()).decode()
        
        login_data = {
            'username': test_user.username,
            'password': encoded_password
        }
        
        # 发送登录请求
        response = api_client.post(
            '/system/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        # 断言响应
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'token' in data['data']
        assert data['data']['token'] != ''
    
    def test_login_invalid_credentials(self, api_client, test_user):
        """
        测试错误的登录凭证
        """
        from base64 import b64encode
        
        # 使用错误的密码
        wrong_password = 'wrongpassword'
        encoded_password = b64encode(wrong_password.encode()).decode()
        
        login_data = {
            'username': test_user.username,
            'password': encoded_password
        }
        
        # 发送登录请求
        response = api_client.post(
            '/system/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        # 断言响应
        assert response.status_code in [401, 403, 400]
        data = response.json()
        assert data['success'] is False
    
    def test_get_user_info_authenticated(self, authenticated_client, test_user):
        """
        测试已认证用户获取用户信息
        """
        response = authenticated_client.get('/system/auth/user/info')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['username'] == test_user.username
    
    def test_get_user_info_unauthenticated(self, api_client):
        """
        测试未认证用户获取用户信息（应该失败）
        """
        response = api_client.get('/system/auth/user/info')
        
        # 未认证应该返回 401 或 403
        assert response.status_code in [401, 403]


# ==================== YAML 验证测试示例 ====================

@pytest.mark.yaml
@pytest.mark.django_db
class TestYamlValidation:
    """
    YAML 验证 API 测试类
    """
    
    def test_validate_valid_yaml(self, authenticated_client, sample_yaml_data):
        """
        测试验证有效的 YAML 数据
        """
        response = authenticated_client.post(
            '/system/yaml/validate',
            data=json.dumps(sample_yaml_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
    
    def test_validate_invalid_yaml(self, authenticated_client):
        """
        测试验证无效的 YAML 数据
        """
        invalid_data = {
            'metadata': {},  # 缺少必需字段
            'hardware': {}   # 缺少必需字段
        }
        
        response = authenticated_client.post(
            '/system/yaml/validate',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        # 可能返回 400 (Bad Request) 或 200 (带错误信息)
        assert response.status_code in [200, 400]
        data = response.json()
        # 如果返回 200，success 应该为 False
        if response.status_code == 200:
            assert data.get('success') is False


# ==================== 参数化测试示例 ====================

@pytest.mark.parametrize("test_input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("python", "PYTHON"),
])
def test_string_upper(test_input, expected):
    """
    参数化测试示例
    """
    assert test_input.upper() == expected


@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (10, 20, 30),
    (-5, 5, 0),
])
def test_addition(a, b, expected):
    """
    参数化测试：加法
    """
    assert a + b == expected


# ==================== Fixture 使用示例 ====================

@pytest.fixture
def sample_data():
    """
    自定义 fixture 示例
    """
    return {
        'key1': 'value1',
        'key2': 'value2',
        'nested': {
            'key3': 'value3'
        }
    }


def test_using_fixture(sample_data):
    """
    使用自定义 fixture
    """
    assert sample_data['key1'] == 'value1'
    assert 'nested' in sample_data
    assert sample_data['nested']['key3'] == 'value3'


# ==================== 异常测试示例 ====================

def test_exception_handling():
    """
    测试异常处理
    """
    with pytest.raises(ValueError):
        int("not a number")
    
    with pytest.raises(ZeroDivisionError):
        1 / 0


# ==================== 慢测试示例 ====================

@pytest.mark.slow
def test_slow_operation():
    """
    标记为慢速测试
    使用 -m "not slow" 可以跳过此测试
    """
    import time
    time.sleep(2)  # 模拟耗时操作
    assert True


# ==================== 跳过测试示例 ====================

@pytest.mark.skip(reason="功能尚未实现")
def test_future_feature():
    """
    跳过测试：功能尚未实现
    """
    assert False  # 这个测试不会执行


@pytest.mark.skipif(
    not hasattr(json, 'some_new_feature'),
    reason="需要新版本的 json 模块"
)
def test_new_json_feature():
    """
    条件跳过测试
    """
    pass

