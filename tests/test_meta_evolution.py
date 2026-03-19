"""Tests for SEMDS meta-evolution (self-improvement) system."""

import json
import tempfile
from pathlib import Path

import pytest

from mother.core.meta_evolution import (
    ImprovementGenerator,
    ImprovementHypothesis,
    MetaEvolutionEngine,
    SafeSelfUpdater,
    SelfExperiment,
    SystemTelemetry,
)


class TestSystemTelemetry:
    """Test system telemetry collection."""
    
    def test_record_observation(self, tmp_path):
        """Test recording an observation."""
        telemetry = SystemTelemetry(storage_dir=str(tmp_path))
        
        telemetry.record("test_metric", 0.85, {"task": "calculator"})
        
        # 检查文件是否创建
        assert (tmp_path / "observations.jsonl").exists()
    
    def test_record_code_generation(self, tmp_path):
        """Test recording code generation event."""
        telemetry = SystemTelemetry(storage_dir=str(tmp_path))
        
        telemetry.record_code_generation(
            task_type="calculator",
            success=True,
            score=1.0,
            generation_time=2.5
        )
        
        # 读取并验证
        with open(tmp_path / "observations.jsonl", "r") as f:
            line = json.loads(f.readline())
            assert line["metric_name"] == "code_generation"
            assert line["metric_value"] == 1.0
            assert line["context"]["task_type"] == "calculator"
    
    def test_analyze_performance_no_data(self, tmp_path):
        """Test analysis with no data."""
        telemetry = SystemTelemetry(storage_dir=str(tmp_path))
        
        result = telemetry.analyze_recent_performance(hours=24)
        
        assert "error" in result
    
    def test_analyze_performance_with_data(self, tmp_path):
        """Test analysis with data."""
        telemetry = SystemTelemetry(storage_dir=str(tmp_path))
        
        # 记录一些数据
        for i in range(3):
            telemetry.record_code_generation(
                task_type="test",
                success=True,
                score=1.0,
                generation_time=2.0
            )
        
        result = telemetry.analyze_recent_performance(hours=24)
        
        assert result["success_rate"] == 1.0
        assert result["total_generations"] == 3


class TestImprovementGenerator:
    """Test improvement hypothesis generation."""
    
    def test_generate_hypotheses_no_opportunities(self, tmp_path):
        """Test with no improvement opportunities."""
        telemetry = SystemTelemetry(storage_dir=str(tmp_path))
        generator = ImprovementGenerator(telemetry)
        
        # 记录成功数据（没有改进空间）
        for i in range(5):
            telemetry.record_code_generation(
                task_type="test",
                success=True,
                score=1.0,
                generation_time=2.0
            )
        
        hypotheses = generator.generate_hypotheses()
        
        # 高成功率，不应该生成假设
        assert len(hypotheses) == 0
    
    def test_generate_hypotheses_with_syntax_errors(self, tmp_path):
        """Test generates hypothesis for syntax errors."""
        telemetry = SystemTelemetry(storage_dir=str(tmp_path))
        generator = ImprovementGenerator(telemetry)
        
        # 记录语法错误
        for i in range(5):
            telemetry.record_code_generation(
                task_type="test",
                success=False,
                score=0.0,
                generation_time=2.0,
                error_type="syntax_error"
            )
        
        hypotheses = generator.generate_hypotheses()
        
        assert len(hypotheses) > 0
        assert any("syntax" in h.description.lower() for h in hypotheses)


class TestSafeSelfUpdater:
    """Test safe self-updater."""
    
    def test_backup_and_update(self, tmp_path):
        """Test backup before update."""
        updater = SafeSelfUpdater(backup_dir=str(tmp_path / "backups"))
        updater.config_file = tmp_path / "config.json"
        
        # 创建初始配置
        updater.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(updater.config_file, "w") as f:
            json.dump({"old": "value"}, f)
        
        # 创建假设和实验结果
        hypothesis = ImprovementHypothesis(
            id="test123",
            description="Test improvement",
            target_component="test",
            proposed_change={"new": "value"},
            expected_improvement=0.1,
            test_scenarios=[]
        )
        
        from mother.core.meta_evolution import ExperimentResult
        experiment = ExperimentResult(
            hypothesis_id="test123",
            control_group_score=0.5,
            treatment_group_score=0.7,
            sample_size=10,
            p_value=0.01,
            is_significant=True
        )
        
        # 应用改进
        result = updater.apply_improvement(hypothesis, experiment)
        
        assert result is True
        
        # 验证配置已更新
        with open(updater.config_file, "r") as f:
            config = json.load(f)
        
        assert config["test"]["new"] == "value"
        assert config["test"]["improvement_id"] == "test123"
    
    def test_reject_non_significant(self, tmp_path):
        """Test rejecting non-significant results."""
        updater = SafeSelfUpdater(backup_dir=str(tmp_path / "backups"))
        
        hypothesis = ImprovementHypothesis(
            id="test456",
            description="Test improvement",
            target_component="test",
            proposed_change={"new": "value"},
            expected_improvement=0.1,
            test_scenarios=[]
        )
        
        from mother.core.meta_evolution import ExperimentResult
        experiment = ExperimentResult(
            hypothesis_id="test456",
            control_group_score=0.5,
            treatment_group_score=0.51,  # 不显著
            sample_size=10,
            p_value=0.5,
            is_significant=False
        )
        
        result = updater.apply_improvement(hypothesis, experiment)
        
        assert result is False


class TestMetaEvolutionEngine:
    """Test meta-evolution engine."""
    
    @pytest.mark.skip(reason="Requires DeepSeek API key")
    def test_initialization(self, tmp_path):
        """Test engine initialization."""
        import os
        os.chdir(tmp_path)
        
        engine = MetaEvolutionEngine()
        
        assert engine.telemetry is not None
        assert engine.improvement_generator is not None
        assert engine.experiment is not None
        assert engine.updater is not None
    
    @pytest.mark.skip(reason="Requires DeepSeek API key")
    def test_record_and_analyze(self, tmp_path):
        """Test recording and analyzing data."""
        import os
        os.chdir(tmp_path)
        
        engine = MetaEvolutionEngine()
        
        # 记录数据
        for i in range(5):
            engine.record_generation_result(
                task_type="test",
                success=False,
                score=0.0,
                generation_time=2.0,
                error_type="syntax_error"
            )
        
        # 分析
        analysis = engine.telemetry.analyze_recent_performance(hours=24)
        
        assert analysis["success_rate"] == 0.0
        assert analysis["error_patterns"]["syntax_error"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
