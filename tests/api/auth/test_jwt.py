"""测试JWT功能"""
import pytest
from datetime import datetime, timezone, timedelta


class TestJWTToken:
    """JWT Token测试"""
    
    def test_create_access_token(self):
        """应能创建访问Token"""
        from api.auth.jwt import create_access_token
        
        token = create_access_token(
            data={"sub": "user-123", "role": "user"}
        )
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_token(self):
        """应能验证有效Token"""
        from api.auth.jwt import create_access_token, verify_token
        
        token = create_access_token(data={"sub": "user-123", "role": "user"})
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["role"] == "user"
    
    def test_verify_expired_token_returns_none(self):
        """过期Token应返回None"""
        from api.auth.jwt import create_access_token, verify_token
        
        # 创建已过期Token（负数过期时间）
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=timedelta(minutes=-1)
        )
        payload = verify_token(token)
        
        assert payload is None
    
    def test_verify_invalid_token_returns_none(self):
        """无效Token应返回None"""
        from api.auth.jwt import verify_token
        
        payload = verify_token("invalid.token.here")
        assert payload is None
    
    def test_token_contains_expiry(self):
        """Token应包含过期时间"""
        from api.auth.jwt import create_access_token, verify_token
        from datetime import datetime
        
        token = create_access_token(data={"sub": "user-123"})
        payload = verify_token(token)
        
        assert "exp" in payload
        # exp应为时间戳
        assert isinstance(payload["exp"], (int, float))
    
    def test_custom_expiry(self):
        """应支持自定义过期时间"""
        from api.auth.jwt import create_access_token, verify_token
        
        # 创建2小时后过期的Token
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=timedelta(hours=2)
        )
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user-123"
