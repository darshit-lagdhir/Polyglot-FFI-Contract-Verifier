import pytest
import sys
import os

sys.path.insert(0, os.path.abspath('modules/module_02_verification_pipeline'))

from verification_pipeline import HookManager, HookContext, HookPoints

@pytest.mark.unit
class TestHookManager:
    """Unit tests for HookManager."""
    
    def test_register_hook(self):
        """Should register hook successfully."""
        manager = HookManager()
        
        def my_hook(context, **kwargs):
            pass
        
        manager.register(HookPoints.PRE_PIPELINE, my_hook)
        
        hooks = manager.list_hooks()
        assert HookPoints.PRE_PIPELINE in hooks
        assert hooks[HookPoints.PRE_PIPELINE] == 1
    
    def test_register_multiple_hooks(self):
        """Should register multiple hooks for same point."""
        manager = HookManager()
        
        def hook1(context, **kwargs):
            pass
        
        def hook2(context, **kwargs):
            pass
        
        manager.register(HookPoints.PRE_PIPELINE, hook1)
        manager.register(HookPoints.PRE_PIPELINE, hook2)
        
        hooks = manager.list_hooks()
        assert hooks[HookPoints.PRE_PIPELINE] == 2
    
    def test_execute_hooks(self):
        """Should execute all registered hooks."""
        manager = HookManager()
        
        executed = []
        
        def hook1(context, **kwargs):
            executed.append('hook1')
        
        def hook2(context, **kwargs):
            executed.append('hook2')
        
        manager.register(HookPoints.PRE_PIPELINE, hook1)
        manager.register(HookPoints.PRE_PIPELINE, hook2)
        
        context = HookContext('test-id', None, {})
        manager.execute(HookPoints.PRE_PIPELINE, context)
        
        assert len(executed) == 2
        assert 'hook1' in executed
        assert 'hook2' in executed
    
    def test_execute_no_hooks(self):
        """Should handle execution when no hooks registered."""
        manager = HookManager()
        
        context = HookContext('test-id', None, {})
                manager.execute(HookPoints.PRE_PIPELINE, context)
    
    def test_hook_failure_doesnt_break_execution(self):
                manager = HookManager()
        
        executed = []
        
        def failing_hook(context, **kwargs):
            raise ValueError("Hook failed")
        
        def success_hook(context, **kwargs):
            executed.append('success')
        
        manager.register(HookPoints.PRE_PIPELINE, failing_hook)
        manager.register(HookPoints.PRE_PIPELINE, success_hook)
        
        context = HookContext('test-id', None, {})
                manager.execute(HookPoints.PRE_PIPELINE, context)
        
        # Success hook should still execute
        assert 'success' in executed
    
    def test_list_hooks_specific_point(self):
        """Should list hooks for specific point."""
        manager = HookManager()
        
        def hook1(context, **kwargs):
            pass
        
        manager.register(HookPoints.PRE_PIPELINE, hook1)
        manager.register(HookPoints.POST_PIPELINE, hook1)
        
        hooks = manager.list_hooks(HookPoints.PRE_PIPELINE)
        assert HookPoints.PRE_PIPELINE in hooks
        assert hooks[HookPoints.PRE_PIPELINE] == 1
