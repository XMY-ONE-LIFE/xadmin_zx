# YAML Test Plan Validation - 独立模块迁移指南

## 📋 概述

本文档说明如何完成 YAML 测试计划验证功能的独立模块集成。

## ✅ 当前状态

- ✅ 已创建独立应用目录：`yaml_test_plan/`
- ✅ 已创建核心验证器：`yaml_test_plan/validator.py`
- ⏳ 待完成：其他文件创建和配置

## 🚀 完成步骤

### 步骤 1：创建剩余的核心文件

在 `yaml_test_plan/` 目录中创建以下文件：

#### 1.1 `models.py`

```python
from django.db import models


class TestPlanYaml(models.Model):
    """YAML测试计划上传与验证"""
    id = models.BigAutoField(primary_key=True, db_comment='ID')
    
    # 文件信息
    file_name = models.CharField(max_length=255, db_comment='文件名')
    file_content = models.TextField(db_comment='文件内容')
    file_size = models.IntegerField(default=0, db_comment='文件大小(字节)')
    
    # 测试计划基本信息
    plan_name = models.CharField(max_length=255, blank=True, null=True, db_comment='计划名称')
    cpu = models.CharField(max_length=100, blank=True, null=True, db_comment='CPU型号')
    gpu = models.CharField(max_length=100, blank=True, null=True, db_comment='GPU型号')
    
    # 验证结果
    analysis_result = models.JSONField(blank=True, null=True, db_comment='分析结果')
    validation_status = models.CharField(
        max_length=20,
        default='valid',
        db_comment='验证状态(valid: 有效; warning: 警告; error: 错误)'
    )
    
    # 元数据
    create_user = models.BigIntegerField(db_comment='创建人')
    create_time = models.DateTimeField(auto_now_add=True, db_comment='创建时间')
    
    class Meta:
        db_table = 'yaml_test_plan'
        db_table_comment = 'YAML测试计划表'
        app_label = 'yaml_test_plan'
        ordering = ['-create_time']
```

#### 1.2 `api.py`

```python
from ninja import Router, File
from ninja.files import UploadedFile
from xadmin_auth.auth import TitwBaseAuth
from .validator import validate_yaml_full
from .models import TestPlanYaml
from django.db import transaction

router = Router(tags=["YAML测试计划验证"])


@router.post("/upload", auth=TitwBaseAuth(), summary="上传YAML测试计划")
def upload_yaml(request, file: UploadedFile = File(...)):
    """上传并验证 YAML 测试计划文件"""
    try:
        # 文件类型检查
        if not file.name.endswith(('.yaml', '.yml')):
            return {
                'code': 400,
                'message': 'Only YAML files (.yaml, .yml) are allowed',
                'data': None
            }
        
        # 文件大小检查 (最大 5MB)
        if file.size > 5 * 1024 * 1024:
            return {
                'code': 400,
                'message': 'File size exceeds 5MB limit',
                'data': None
            }
        
        # 读取内容
        content = file.read().decode('utf-8')
        
        # 严格验证
        validation_result = validate_yaml_full(content)
        
        if not validation_result['valid']:
            error_message = validation_result['error_message']
            line_number = validation_result.get('line_number')
            
            if line_number:
                display_message = f"Line {line_number} [ERROR]\\n{error_message}"
            else:
                display_message = f"[ERROR]\\n{error_message}"
            
            return {
                'code': 400,
                'message': 'YAML Validation Failed',
                'data': {
                    'error_code': validation_result.get('error_code'),
                    'error_message': display_message,
                    'line_number': line_number
                }
            }
        
        # 验证通过，保存到数据库
        with transaction.atomic():
            yaml_record = TestPlanYaml.objects.create(
                file_name=file.name,
                file_content=content,
                file_size=file.size,
                validation_status='valid',
                create_user=request.user.id
            )
        
        return {
            'code': 200,
            'message': 'File uploaded and validated successfully',
            'data': {
                'id': yaml_record.id,
                'file_name': yaml_record.file_name,
                'file_size': yaml_record.file_size
            }
        }
    
    except Exception as e:
        return {
            'code': 500,
            'message': f'Server error: {str(e)}',
            'data': None
        }


@router.get("/list", auth=TitwBaseAuth(), summary="获取YAML列表")
def list_yaml(request, page: int = 1, page_size: int = 10):
    """获取 YAML 测试计划列表"""
    try:
        offset = (page - 1) * page_size
        queryset = TestPlanYaml.objects.all()
        total = queryset.count()
        records = queryset[offset:offset + page_size]
        
        data_list = []
        for record in records:
            data_list.append({
                'id': record.id,
                'file_name': record.file_name,
                'file_size': record.file_size,
                'validation_status': record.validation_status,
                'create_time': record.create_time.isoformat(),
            })
        
        return {
            'code': 200,
            'message': 'Success',
            'data': {
                'list': data_list,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        }
    except Exception as e:
        return {
            'code': 500,
            'message': f'Server error: {str(e)}',
            'data': None
        }
```

#### 1.3 `urls.py`

```python
from django.urls import path
from .api import router

urlpatterns = [
    path('api/', router.urls),
]
```

### 步骤 2：注册应用

编辑 `xadmin/settings.py`，在 `INSTALLED_APPS` 中添加：

```python
INSTALLED_APPS = [
    # ... 其他应用 ...
    'yaml_test_plan',  # 新增
]
```

### 步骤 3：添加路由

编辑 `xadmin/urls.py`，添加：

```python
from django.urls import path, include

urlpatterns = [
    # ... 其他路由 ...
    path('api/yaml-test-plan/', include('yaml_test_plan.urls')),  # 新增
]
```

### 步骤 4：数据库迁移

```bash
# 创建迁移文件
python manage.py makemigrations yaml_test_plan

# 应用迁移
python manage.py migrate yaml_test_plan
```

### 步骤 5：测试

```bash
# 启动服务器
python manage.py runserver

# 测试 API
curl -X POST http://localhost:8000/api/yaml-test-plan/api/upload \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -F "file=@test.yaml"
```

### 步骤 6：提交到 Git

```bash
git add yaml_test_plan/
git add xadmin/settings.py
git add xadmin/urls.py
git add YAML_MIGRATION_GUIDE.md

git commit -m "feat: add independent YAML test plan validation module

- Create standalone yaml_test_plan app
- Implement strict YAML validation (ported from TPGen.html)
- Add validation API endpoints
- Add database model for YAML records
- No conflicts with existing code"

git push -u myfork feature/yaml-validation-module
```

## 📝 API 文档

### 上传验证 YAML

**Endpoint**: `POST /api/yaml-test-plan/api/upload`

**Headers**:
- `Authorization`: Bearer token

**Body**: `multipart/form-data`
- `file`: YAML 文件

**Response** (成功):
```json
{
  "code": 200,
  "message": "File uploaded and validated successfully",
  "data": {
    "id": 1,
    "file_name": "test.yaml",
    "file_size": 1234
  }
}
```

**Response** (验证失败):
```json
{
  "code": 400,
  "message": "YAML Validation Failed",
  "data": {
    "error_code": "E001",
    "error_message": "Line 10 [ERROR]\\nE001 Unsupported: missing mandatory field...",
    "line_number": 10
  }
}
```

### 获取YAML列表

**Endpoint**: `GET /api/yaml-test-plan/api/list?page=1&page_size=10`

**Headers**:
- `Authorization`: Bearer token

**Response**:
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "list": [...],
    "total": 100,
    "page": 1,
    "page_size": 10
  }
}
```

## 🎯 优势

✅ **完全独立**：不修改任何现有模块（`xadmin_auth`、`xadmin_db`）  
✅ **零冲突**：不会与同事的代码产生冲突  
✅ **易于维护**：模块化设计，清晰的职责划分  
✅ **易于审查**：PR 只包含新增文件，无修改现有文件  

## ❓ 问题排查

### Q: 导入错误
A: 确保 `yaml_test_plan` 在 `INSTALLED_APPS` 中

### Q: 数据库错误
A: 运行 `python manage.py migrate yaml_test_plan`

### Q: API 404
A: 检查 `xadmin/urls.py` 中的路由配置

## 📞 联系

如有问题，请联系开发者。

