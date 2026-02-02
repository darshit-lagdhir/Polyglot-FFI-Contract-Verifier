import pytest
import sys
import os

sys.path.insert(0, os.path.abspath('modules/module_02_verification_pipeline'))

from verification_pipeline import (
    CompletePipeline,
    OptimizedCompletePipeline,
    ExtensiblePipeline
)

@pytest.mark.integration
class TestPipelineIntegration:
    """Integration tests for pipeline components."""
    
    def test_complete_pipeline_initialization(self, temp_dir):
        """CompletePipeline should initialize correctly."""
        header = temp_dir / "test.h"
        library = temp_dir / "test.dll"
        
        header.write_text("#ifndef TEST_H\n#define TEST_H\n#endif")
        library.write_text("")
        
        try:
            pipeline = CompletePipeline(
                str(header),
                str(library),
                str(temp_dir / "output")
            )
            
            assert pipeline is not None
            assert hasattr(pipeline, 'execute')
            
        except Exception as e:
            # Expected if libclang not available
            if "libclang" in str(e).lower():
                pytest.skip("libclang not available")
            else:
                raise
    
    def test_optimized_pipeline_initialization(self, temp_dir):
        """OptimizedCompletePipeline should initialize correctly."""
        header = temp_dir / "test.h"
        library = temp_dir / "test.dll"
        
        header.write_text("#ifndef TEST_H\n#define TEST_H\n#endif")
        library.write_text("")
        
        try:
            pipeline = OptimizedCompletePipeline(
                str(header),
                str(library),
                str(temp_dir / "output"),
                cache_enabled=True,
                parallel=False
            )
            
            assert pipeline is not None
            assert hasattr(pipeline, 'cache_manager')
            
        except Exception as e:
            if "libclang" in str(e).lower():
                pytest.skip("libclang not available")
            else:
                raise
    
    def test_extensible_pipeline_initialization(self, temp_dir):
        """ExtensiblePipeline should initialize correctly."""
        header = temp_dir / "test.h"
        library = temp_dir / "test.dll"
        
        header.write_text("#ifndef TEST_H\n#define TEST_H\n#endif")
        library.write_text("")
        
        try:
            pipeline = ExtensiblePipeline(
                str(header),
                str(library),
                str(temp_dir / "output")
            )
            
            assert pipeline is not None
            assert hasattr(pipeline, 'rule_registry')
            assert hasattr(pipeline, 'hook_manager')
            assert hasattr(pipeline, 'plugin_manager')
            
        except Exception as e:
            if "libclang" in str(e).lower():
                pytest.skip("libclang not available")
            else:
                raise

@pytest.mark.integration
class TestPluginIntegration:
    """Integration tests for plugin system."""
    
    def test_plugin_registration(self, temp_dir):
        """Plugin should register successfully."""
        from verification_pipeline import PipelinePlugin
        
        class TestPlugin(PipelinePlugin):
            PLUGIN_NAME = "test_plugin"
            PLUGIN_VERSION = "1.0.0"
            
            def initialize(self, pipeline):
                self.pipeline = pipeline
        
        header = temp_dir / "test.h"
        library = temp_dir / "test.dll"
        
        header.write_text("#ifndef TEST_H\n#define TEST_H\n#endif")
        library.write_text("")
        
        try:
            pipeline = ExtensiblePipeline(
                str(header),
                str(library),
                str(temp_dir / "output")
            )
            
            plugin = TestPlugin()
            pipeline.register_plugin(plugin)
            
            plugins = pipeline.plugin_manager.list_plugins()
            assert len(plugins) == 1
            assert plugins[0]['name'] == 'test_plugin'
            
        except Exception as e:
            if "libclang" in str(e).lower():
                pytest.skip("libclang not available")
            else:
                raise
