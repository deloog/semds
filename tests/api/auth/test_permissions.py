"""测试权限模型"""


class TestTaskPermissions:
    """任务权限测试"""

    def test_task_permissions_defined(self):
        """应定义任务相关权限"""
        from api.auth.permissions import TaskPermission

        assert hasattr(TaskPermission, "CREATE")
        assert hasattr(TaskPermission, "READ")
        assert hasattr(TaskPermission, "UPDATE")
        assert hasattr(TaskPermission, "DELETE")
        assert hasattr(TaskPermission, "CONTROL")

    def test_task_permission_values(self):
        """任务权限值应为正确字符串"""
        from api.auth.permissions import TaskPermission

        assert TaskPermission.CREATE == "task:create"
        assert TaskPermission.READ == "task:read"
        assert TaskPermission.UPDATE == "task:update"
        assert TaskPermission.DELETE == "task:delete"
        assert TaskPermission.CONTROL == "task:control"


class TestApprovalPermissions:
    """审批权限测试"""

    def test_approval_permissions_defined(self):
        """应定义审批相关权限"""
        from api.auth.permissions import ApprovalPermission

        assert hasattr(ApprovalPermission, "CREATE")
        assert hasattr(ApprovalPermission, "READ")
        assert hasattr(ApprovalPermission, "APPROVE")
        assert hasattr(ApprovalPermission, "REJECT")

    def test_approval_permission_values(self):
        """审批权限值应为正确字符串"""
        from api.auth.permissions import ApprovalPermission

        assert ApprovalPermission.CREATE == "approval:create"
        assert ApprovalPermission.READ == "approval:read"
        assert ApprovalPermission.APPROVE == "approval:approve"
        assert ApprovalPermission.REJECT == "approval:reject"


class TestRolePermissions:
    """角色权限映射测试"""

    def test_user_role_has_correct_permissions(self):
        """USER角色应有正确的权限集合"""
        from api.auth.models import UserRole
        from api.auth.permissions import (
            ApprovalPermission,
            RolePermissions,
            TaskPermission,
        )

        user_perms = RolePermissions.get_permissions(UserRole.USER)

        # USER 应有这些权限
        assert TaskPermission.READ in user_perms
        assert TaskPermission.CREATE in user_perms
        assert TaskPermission.UPDATE in user_perms
        assert TaskPermission.CONTROL in user_perms
        assert ApprovalPermission.READ in user_perms
        assert ApprovalPermission.APPROVE in user_perms
        assert ApprovalPermission.REJECT in user_perms

        # USER 不应有这些权限
        assert TaskPermission.DELETE not in user_perms
        assert ApprovalPermission.CREATE not in user_perms

    def test_admin_role_has_all_permissions(self):
        """ADMIN角色应拥有所有权限"""
        from api.auth.models import UserRole
        from api.auth.permissions import (
            ApprovalPermission,
            RolePermissions,
            TaskPermission,
        )

        admin_perms = RolePermissions.get_permissions(UserRole.ADMIN)

        # Admin 拥有所有任务权限
        assert TaskPermission.CREATE in admin_perms
        assert TaskPermission.READ in admin_perms
        assert TaskPermission.UPDATE in admin_perms
        assert TaskPermission.DELETE in admin_perms
        assert TaskPermission.CONTROL in admin_perms

        # Admin 拥有所有审批权限
        assert ApprovalPermission.CREATE in admin_perms
        assert ApprovalPermission.READ in admin_perms
        assert ApprovalPermission.APPROVE in admin_perms
        assert ApprovalPermission.REJECT in admin_perms

    def test_has_permission_check(self):
        """has_permission 方法应正确检查权限"""
        from api.auth.models import UserRole
        from api.auth.permissions import (
            ApprovalPermission,
            RolePermissions,
            TaskPermission,
        )

        # USER 有 READ 权限
        assert (
            RolePermissions.has_permission(UserRole.USER, TaskPermission.READ) is True
        )
        # USER 没有 DELETE 权限
        assert (
            RolePermissions.has_permission(UserRole.USER, TaskPermission.DELETE)
            is False
        )
        # USER 没有 CREATE approval 权限
        assert (
            RolePermissions.has_permission(UserRole.USER, ApprovalPermission.CREATE)
            is False
        )

        # ADMIN 有所有权限
        assert (
            RolePermissions.has_permission(UserRole.ADMIN, TaskPermission.DELETE)
            is True
        )
        assert (
            RolePermissions.has_permission(UserRole.ADMIN, ApprovalPermission.CREATE)
            is True
        )

    def test_get_permissions_returns_set(self):
        """get_permissions 应返回集合类型"""
        from api.auth.models import UserRole
        from api.auth.permissions import RolePermissions

        perms = RolePermissions.get_permissions(UserRole.USER)
        assert isinstance(perms, set)

    def test_get_permissions_unknown_role_returns_empty_set(self):
        """未知角色应返回空集合"""
        from api.auth.permissions import RolePermissions

        # 使用不存在的角色值
        perms = RolePermissions.get_permissions("unknown_role")
        assert perms == set()
