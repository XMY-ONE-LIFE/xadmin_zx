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
    
    def __str__(self):
        return f'<{self.id}, {self.file_name}>'

