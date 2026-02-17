"""Test Suite for Language Adapter - Prompt 13/25: 90 tests."""

import json
import pytest
from modules.module_08_language_adapter import (
    ContractMetadata,
    StateSnapshot,
    HistoryTracker,
    QueryEngine,
    MetadataEnricher,
    IntrospectionAPI,
    PythonAdapterComplete,
    ViolationReport,
    EnforcementContext,
    ClauseSeverity,
    ValidationGraph,
    ValidationNode,
)


# ════════════════════════════════════════════════════════════════════════════
# CONTRACT METADATA TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestContractMetadata:
    """ContractMetadata tests (15 tests)."""

    def test_create_metadata(self):
        """Test 1106: Create contract metadata."""
        metadata = ContractMetadata(contract_id='test_contract')
        assert metadata.contract_id == 'test_contract'

    def test_metadata_default_version(self):
        """Test 1107: Default version is 1.0.0."""
        metadata = ContractMetadata('test')
        assert metadata.version == '1.0.0'

    def test_metadata_with_version(self):
        """Test 1108: Metadata with custom version."""
        metadata = ContractMetadata('test', version='2.0.0')
        assert metadata.version == '2.0.0'

    def test_metadata_with_author(self):
        """Test 1109: Metadata with author."""
        metadata = ContractMetadata('test', author='Test Author')
        assert metadata.author == 'Test Author'

    def test_add_function_metadata(self):
        """Test 1110: Add function metadata."""
        metadata = ContractMetadata('test')
        metadata.add_function_metadata('func1', {'description': 'Test fn'})

        func_meta = metadata.get_function_metadata('func1')
        assert func_meta['description'] == 'Test fn'

    def test_get_nonexistent_function_metadata(self):
        """Test 1111: Get nonexistent function metadata."""
        metadata = ContractMetadata('test')
        assert metadata.get_function_metadata('missing') is None

    def test_metadata_to_dict(self):
        """Test 1112: Metadata to dict."""
        metadata = ContractMetadata(
            'test', version='1.0.0', author='Author'
        )
        data = metadata.to_dict()

        assert data['contract_id'] == 'test'
        assert data['version'] == '1.0.0'
        assert data['author'] == 'Author'

    def test_metadata_to_dict_all_fields(self):
        """Test 1113: All fields in dict."""
        metadata = ContractMetadata('test')
        data = metadata.to_dict()

        expected_keys = [
            'contract_id', 'version', 'author', 'created_at',
            'description', 'source_file', 'function_metadata',
            'supported_platforms', 'min_language_version',
            'performance_hints', 'security_level', 'requires_encryption'
        ]
        for key in expected_keys:
            assert key in data

    def test_metadata_default_security(self):
        """Test 1114: Default security level is standard."""
        metadata = ContractMetadata('test')
        assert metadata.security_level == 'standard'

    def test_metadata_default_encryption(self):
        """Test 1115: Default encryption is False."""
        metadata = ContractMetadata('test')
        assert metadata.requires_encryption is False

    def test_metadata_supported_platforms(self):
        """Test 1116: Supported platforms."""
        metadata = ContractMetadata(
            'test',
            supported_platforms=['linux', 'windows']
        )
        assert 'linux' in metadata.supported_platforms
        assert 'windows' in metadata.supported_platforms

    def test_metadata_performance_hints(self):
        """Test 1117: Performance hints."""
        metadata = ContractMetadata(
            'test',
            performance_hints={'cache_results': True}
        )
        assert metadata.performance_hints['cache_results'] is True

    def test_metadata_description(self):
        """Test 1118: Description field."""
        metadata = ContractMetadata(
            'test', description='Test contract'
        )
        assert metadata.description == 'Test contract'

    def test_metadata_source_file(self):
        """Test 1119: Source file field."""
        metadata = ContractMetadata(
            'test', source_file='contract.json'
        )
        assert metadata.source_file == 'contract.json'

    def test_multiple_function_metadata(self):
        """Test 1120: Multiple function metadata entries."""
        metadata = ContractMetadata('test')
        metadata.add_function_metadata('func1', {'desc': 'one'})
        metadata.add_function_metadata('func2', {'desc': 'two'})

        assert metadata.get_function_metadata('func1')['desc'] == 'one'
        assert metadata.get_function_metadata('func2')['desc'] == 'two'


# ════════════════════════════════════════════════════════════════════════════
# STATE SNAPSHOT TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestStateSnapshot:
    """StateSnapshot tests (10 tests)."""

    def test_create_snapshot(self):
        """Test 1121: Create state snapshot."""
        snapshot = StateSnapshot(timestamp='2024-01-01T00:00:00Z')
        assert snapshot.timestamp == '2024-01-01T00:00:00Z'

    def test_snapshot_with_functions(self):
        """Test 1122: Snapshot with loaded functions."""
        snapshot = StateSnapshot(
            timestamp='ts',
            loaded_functions=['func1', 'func2']
        )
        assert len(snapshot.loaded_functions) == 2

    def test_snapshot_to_dict(self):
        """Test 1123: Snapshot to dict."""
        snapshot = StateSnapshot(timestamp='ts')
        data = snapshot.to_dict()
        assert 'timestamp' in data
        assert 'loaded_functions' in data

    def test_snapshot_to_json(self):
        """Test 1124: Snapshot to JSON."""
        snapshot = StateSnapshot(timestamp='ts')
        json_str = snapshot.to_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed['timestamp'] == 'ts'

    def test_snapshot_empty_defaults(self):
        """Test 1125: Snapshot empty defaults."""
        snapshot = StateSnapshot(timestamp='ts')
        assert snapshot.active_invocations == []
        assert snapshot.ownership_state == {}
        assert snapshot.configuration == {}
        assert snapshot.statistics == {}
        assert snapshot.loaded_functions == []

    def test_snapshot_with_invocations(self):
        """Test 1126: Snapshot with active invocations."""
        snapshot = StateSnapshot(
            timestamp='ts',
            active_invocations=[{'func': 'test'}]
        )
        assert len(snapshot.active_invocations) == 1

    def test_snapshot_with_ownership(self):
        """Test 1127: Snapshot with ownership state."""
        snapshot = StateSnapshot(
            timestamp='ts',
            ownership_state={'active': 5}
        )
        assert snapshot.ownership_state['active'] == 5

    def test_snapshot_with_config(self):
        """Test 1128: Snapshot with configuration."""
        snapshot = StateSnapshot(
            timestamp='ts',
            configuration={'mode': 'strict'}
        )
        assert snapshot.configuration['mode'] == 'strict'

    def test_snapshot_with_statistics(self):
        """Test 1129: Snapshot with statistics."""
        snapshot = StateSnapshot(
            timestamp='ts',
            statistics={'total': 100}
        )
        assert snapshot.statistics['total'] == 100

    def test_snapshot_json_indent(self):
        """Test 1130: Snapshot JSON with custom indent."""
        snapshot = StateSnapshot(timestamp='ts')
        json_str = snapshot.to_json(indent=4)
        assert '    ' in json_str


# ════════════════════════════════════════════════════════════════════════════
# HISTORY TRACKER TESTS (20 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestHistoryTracker:
    """HistoryTracker tests (20 tests)."""

    def test_create_tracker(self):
        """Test 1131: Create history tracker."""
        tracker = HistoryTracker()
        assert len(tracker.invocations) == 0
        assert len(tracker.violations) == 0
        assert len(tracker.state_changes) == 0

    def test_custom_max_history(self):
        """Test 1132: Custom max history."""
        tracker = HistoryTracker(max_history=50)
        assert tracker.max_history == 50

    def test_record_invocation(self):
        """Test 1133: Record invocation."""
        tracker = HistoryTracker()
        tracker.record_invocation('func1', True, 10.5)

        assert len(tracker.invocations) == 1
        assert tracker.invocations[0]['function_name'] == 'func1'
        assert tracker.invocations[0]['success'] is True
        assert tracker.invocations[0]['duration_ms'] == 10.5

    def test_record_invocation_with_context(self):
        """Test 1134: Record invocation with context."""
        tracker = HistoryTracker()
        context = EnforcementContext('func1', 'uuid-123')
        tracker.record_invocation('func1', True, 10.0, context)

        assert tracker.invocations[0]['context_id'] == 'uuid-123'

    def test_record_invocation_no_context(self):
        """Test 1135: Record invocation without context."""
        tracker = HistoryTracker()
        tracker.record_invocation('func1', True, 10.0)

        assert tracker.invocations[0]['context_id'] is None

    def test_record_violation(self):
        """Test 1136: Record violation."""
        tracker = HistoryTracker()
        tracker.record_violation('func1', 'clause1', 'Bad value')

        assert len(tracker.violations) == 1
        assert tracker.violations[0]['clause_id'] == 'clause1'
        assert tracker.violations[0]['message'] == 'Bad value'

    def test_record_state_change(self):
        """Test 1137: Record state change."""
        tracker = HistoryTracker()
        tracker.record_state_change(
            'ownership_transfer', {'from': 'caller', 'to': 'callee'}
        )

        assert len(tracker.state_changes) == 1
        assert tracker.state_changes[0]['change_type'] == 'ownership_transfer'

    def test_get_recent_invocations(self):
        """Test 1138: Get recent invocations."""
        tracker = HistoryTracker()
        for i in range(20):
            tracker.record_invocation(f'func{i}', True, 10.0)

        recent = tracker.get_recent_invocations(5)
        assert len(recent) == 5
        assert recent[-1]['function_name'] == 'func19'

    def test_get_recent_violations(self):
        """Test 1139: Get recent violations."""
        tracker = HistoryTracker()
        for i in range(10):
            tracker.record_violation(f'func{i}', 'c1', 'msg')

        recent = tracker.get_recent_violations(3)
        assert len(recent) == 3

    def test_invocation_statistics_empty(self):
        """Test 1140: Empty statistics."""
        tracker = HistoryTracker()
        stats = tracker.get_invocation_statistics()

        assert stats['total'] == 0
        assert stats['successful'] == 0
        assert stats['failed'] == 0
        assert stats['success_rate'] == 0.0

    def test_invocation_statistics(self):
        """Test 1141: Invocation statistics."""
        tracker = HistoryTracker()
        tracker.record_invocation('func1', True, 10.0)
        tracker.record_invocation('func2', False, 5.0)
        tracker.record_invocation('func3', True, 15.0)

        stats = tracker.get_invocation_statistics()
        assert stats['total'] == 3
        assert stats['successful'] == 2
        assert stats['failed'] == 1
        assert stats['success_rate'] == pytest.approx(2/3)

    def test_invocation_statistics_average_duration(self):
        """Test 1142: Average duration in statistics."""
        tracker = HistoryTracker()
        tracker.record_invocation('func1', True, 10.0)
        tracker.record_invocation('func2', True, 20.0)

        stats = tracker.get_invocation_statistics()
        assert stats['average_duration_ms'] == 15.0

    def test_max_history_invocations(self):
        """Test 1143: Max history enforced for invocations."""
        tracker = HistoryTracker(max_history=5)

        for i in range(10):
            tracker.record_invocation(f'func{i}', True, 10.0)

        assert len(tracker.invocations) == 5
        assert tracker.invocations[0]['function_name'] == 'func5'

    def test_max_history_violations(self):
        """Test 1144: Max history enforced for violations."""
        tracker = HistoryTracker(max_history=3)

        for i in range(7):
            tracker.record_violation(f'func{i}', 'c1', 'msg')

        assert len(tracker.violations) == 3

    def test_max_history_state_changes(self):
        """Test 1145: Max history enforced for state changes."""
        tracker = HistoryTracker(max_history=4)

        for i in range(8):
            tracker.record_state_change('change', {'i': i})

        assert len(tracker.state_changes) == 4

    def test_clear_history(self):
        """Test 1146: Clear history."""
        tracker = HistoryTracker()
        tracker.record_invocation('func1', True, 10.0)
        tracker.record_violation('func1', 'c1', 'msg')
        tracker.record_state_change('change', {})

        tracker.clear_history()

        assert len(tracker.invocations) == 0
        assert len(tracker.violations) == 0
        assert len(tracker.state_changes) == 0

    def test_invocation_has_timestamp(self):
        """Test 1147: Invocations have timestamps."""
        tracker = HistoryTracker()
        tracker.record_invocation('func1', True, 10.0)

        assert 'timestamp' in tracker.invocations[0]
        assert tracker.invocations[0]['timestamp'].endswith('Z')

    def test_violation_has_timestamp(self):
        """Test 1148: Violations have timestamps."""
        tracker = HistoryTracker()
        tracker.record_violation('func1', 'c1', 'msg')

        assert 'timestamp' in tracker.violations[0]

    def test_state_change_has_timestamp(self):
        """Test 1149: State changes have timestamps."""
        tracker = HistoryTracker()
        tracker.record_state_change('change', {})

        assert 'timestamp' in tracker.state_changes[0]

    def test_recent_invocations_fewer_than_count(self):
        """Test 1150: Recent invocations when fewer than requested."""
        tracker = HistoryTracker()
        tracker.record_invocation('func1', True, 10.0)

        recent = tracker.get_recent_invocations(100)
        assert len(recent) == 1


# ════════════════════════════════════════════════════════════════════════════
# QUERY ENGINE TESTS (20 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestQueryEngine:
    """QueryEngine tests (20 tests)."""

    @pytest.fixture
    def adapter_with_contract(self):
        """Create adapter with validation graph."""
        adapter = PythonAdapterComplete()

        graph = ValidationGraph('test_func')
        node = ValidationNode('c1', 'test', ClauseSeverity.MANDATORY)
        graph.add_node(node)
        adapter.validation_graphs['test_func'] = graph

        return adapter

    def test_create_query_engine(self, adapter_with_contract):
        """Test 1151: Create query engine."""
        engine = QueryEngine(adapter_with_contract)
        assert engine.adapter is adapter_with_contract

    def test_query_contract_functions(self, adapter_with_contract):
        """Test 1152: Query contract functions."""
        engine = QueryEngine(adapter_with_contract)
        functions = engine.query('contract.functions')

        assert 'test_func' in functions

    def test_query_contract_root(self, adapter_with_contract):
        """Test 1153: Query contract root."""
        engine = QueryEngine(adapter_with_contract)
        result = engine.query('contract')

        assert 'functions' in result
        assert 'fingerprint' in result

    def test_query_function_info(self, adapter_with_contract):
        """Test 1154: Query function info."""
        engine = QueryEngine(adapter_with_contract)
        info = engine.query('contract.function.test_func')

        assert info['name'] == 'test_func'
        assert info['clauses'] == 1

    def test_query_function_clause_ids(self, adapter_with_contract):
        """Test 1155: Query function clause IDs."""
        engine = QueryEngine(adapter_with_contract)
        info = engine.query('contract.function.test_func')

        assert 'c1' in info['clause_ids']

    def test_query_function_parameters(self, adapter_with_contract):
        """Test 1156: Query function parameters."""
        engine = QueryEngine(adapter_with_contract)
        result = engine.query(
            'contract.function.test_func.parameters'
        )

        assert isinstance(result, list)

    def test_query_nonexistent_function(self, adapter_with_contract):
        """Test 1157: Query nonexistent function."""
        engine = QueryEngine(adapter_with_contract)
        result = engine.query('contract.function.missing')

        assert result is None

    def test_query_statistics(self, adapter_with_contract):
        """Test 1158: Query statistics."""
        engine = QueryEngine(adapter_with_contract)
        stats = engine.query('stats')

        assert stats is not None
        assert 'loaded_functions' in stats

    def test_query_state_root(self, adapter_with_contract):
        """Test 1159: Query state root."""
        engine = QueryEngine(adapter_with_contract)
        state = engine.query('state')

        assert 'has_contract' in state
        assert 'loaded_functions' in state

    def test_query_state_ownership(self, adapter_with_contract):
        """Test 1160: Query state ownership allocations."""
        engine = QueryEngine(adapter_with_contract)
        result = engine.query('state.ownership.allocations')

        assert isinstance(result, dict)

    def test_query_config(self, adapter_with_contract):
        """Test 1161: Query configuration."""
        engine = QueryEngine(adapter_with_contract)
        config = engine.query('config')

        assert config is not None
        assert 'mode' in config

    def test_query_config_nested(self, adapter_with_contract):
        """Test 1162: Query nested configuration."""
        engine = QueryEngine(adapter_with_contract)
        mode = engine.query('config.mode')

        assert mode is not None

    def test_query_invalid_root_raises(self, adapter_with_contract):
        """Test 1163: Invalid query root raises."""
        engine = QueryEngine(adapter_with_contract)

        with pytest.raises(ValueError, match='Unknown query root'):
            engine.query('invalid.path')

    def test_query_empty_path_raises(self, adapter_with_contract):
        """Test 1164: Empty query path raises."""
        engine = QueryEngine(adapter_with_contract)

        with pytest.raises(ValueError, match='Empty query'):
            engine.query('')

    def test_query_stats_loaded_functions(self, adapter_with_contract):
        """Test 1165: Query stats loaded_functions."""
        engine = QueryEngine(adapter_with_contract)
        result = engine.query('stats.loaded_functions')

        assert isinstance(result, int)
        assert result >= 1

    def test_query_stats_nonexistent_path(self, adapter_with_contract):
        """Test 1166: Query nonexistent stats path returns None."""
        engine = QueryEngine(adapter_with_contract)
        result = engine.query('stats.nonexistent')

        assert result is None

    def test_query_config_nonexistent_path(self, adapter_with_contract):
        """Test 1167: Query nonexistent config path returns None."""
        engine = QueryEngine(adapter_with_contract)
        result = engine.query('config.nonexistent')

        assert result is None

    def test_query_state_nonexistent_path(self, adapter_with_contract):
        """Test 1168: Query nonexistent state path returns None."""
        engine = QueryEngine(adapter_with_contract)
        result = engine.query('state.nonexistent')

        assert result is None

    def test_query_contract_nonexistent_path(self, adapter_with_contract):
        """Test 1169: Query nonexistent contract path returns None."""
        engine = QueryEngine(adapter_with_contract)
        result = engine.query('contract.nonexistent')

        assert result is None

    def test_multiple_functions(self):
        """Test 1170: Query multiple functions."""
        adapter = PythonAdapterComplete()

        for name in ['func_a', 'func_b', 'func_c']:
            graph = ValidationGraph(name)
            node = ValidationNode('c1', 'test', ClauseSeverity.MANDATORY)
            graph.add_node(node)
            adapter.validation_graphs[name] = graph

        engine = QueryEngine(adapter)
        functions = engine.query('contract.functions')

        assert len(functions) == 3
        assert 'func_a' in functions
        assert 'func_b' in functions
        assert 'func_c' in functions


# ════════════════════════════════════════════════════════════════════════════
# METADATA ENRICHER TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestMetadataEnricher:
    """MetadataEnricher tests (10 tests)."""

    def test_create_enricher_no_metadata(self):
        """Test 1171: Create enricher without metadata."""
        enricher = MetadataEnricher()
        assert enricher.metadata is None

    def test_create_enricher_with_metadata(self):
        """Test 1172: Create enricher with metadata."""
        metadata = ContractMetadata('test')
        enricher = MetadataEnricher(metadata)
        assert enricher.metadata is metadata

    def test_enrich_violation_with_metadata(self):
        """Test 1173: Enrich violation report with metadata."""
        metadata = ContractMetadata('test')
        metadata.add_function_metadata('func1', {
            'description': 'Test function',
            'docs_url': 'http://docs.example.com'
        })

        enricher = MetadataEnricher(metadata)

        report = ViolationReport(
            'func1', 'c1', 'type', ClauseSeverity.MANDATORY,
            'exp', 'obs', 'msg', 'fp', 'ts'
        )

        enriched = enricher.enrich_violation_report(report)
        assert enriched['function_description'] == 'Test function'
        assert enriched['documentation_url'] == 'http://docs.example.com'

    def test_enrich_violation_no_metadata(self):
        """Test 1174: Enrich violation without metadata."""
        enricher = MetadataEnricher()

        report = ViolationReport(
            'func1', 'c1', 'type', ClauseSeverity.MANDATORY,
            'exp', 'obs', 'msg', 'fp', 'ts'
        )

        enriched = enricher.enrich_violation_report(report)
        assert 'function_name' in enriched
        assert 'function_description' not in enriched

    def test_enrich_violation_unknown_function(self):
        """Test 1175: Enrich violation for unknown function."""
        metadata = ContractMetadata('test')
        enricher = MetadataEnricher(metadata)

        report = ViolationReport(
            'unknown_func', 'c1', 'type', ClauseSeverity.MANDATORY,
            'exp', 'obs', 'msg', 'fp', 'ts'
        )

        enriched = enricher.enrich_violation_report(report)
        assert 'function_description' not in enriched

    def test_enrich_enforcement_context(self):
        """Test 1176: Enrich enforcement context."""
        metadata = ContractMetadata('test')
        metadata.add_function_metadata('func1', {
            'description': 'Test function',
            'call_frequency': 'high',
            'performance_hint': 'cache results'
        })

        enricher = MetadataEnricher(metadata)
        context = EnforcementContext('func1', 'uuid-1')

        enriched = enricher.enrich_enforcement_context(context)
        assert 'metadata' in enriched
        assert enriched['metadata']['description'] == 'Test function'
        assert enriched['metadata']['expected_frequency'] == 'high'

    def test_enrich_context_no_metadata(self):
        """Test 1177: Enrich context without metadata."""
        enricher = MetadataEnricher()
        context = EnforcementContext('func1', 'uuid-1')

        enriched = enricher.enrich_enforcement_context(context)
        assert 'metadata' not in enriched

    def test_enrich_context_unknown_function(self):
        """Test 1178: Enrich context for unknown function."""
        metadata = ContractMetadata('test')
        enricher = MetadataEnricher(metadata)
        context = EnforcementContext('unknown', 'uuid-1')

        enriched = enricher.enrich_enforcement_context(context)
        assert 'metadata' not in enriched

    def test_enriched_violation_preserves_original(self):
        """Test 1179: Enriched violation preserves original fields."""
        metadata = ContractMetadata('test')
        enricher = MetadataEnricher(metadata)

        report = ViolationReport(
            'func1', 'c1', 'range_check', ClauseSeverity.MANDATORY,
            'x > 0', 'x = -1', 'Violation', 'fp123', 'ts'
        )

        enriched = enricher.enrich_violation_report(report)
        assert enriched['function_name'] == 'func1'
        assert enriched['clause_id'] == 'c1'
        assert enriched['message'] == 'Violation'

    def test_enriched_context_preserves_original(self):
        """Test 1180: Enriched context preserves original fields."""
        metadata = ContractMetadata('test')
        enricher = MetadataEnricher(metadata)
        context = EnforcementContext('func1', 'uuid-1')

        enriched = enricher.enrich_enforcement_context(context)
        assert enriched['function_name'] == 'func1'
        assert enriched['invocation_id'] == 'uuid-1'


# ════════════════════════════════════════════════════════════════════════════
# INTROSPECTION API TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestIntrospectionAPI:
    """IntrospectionAPI tests (15 tests)."""

    @pytest.fixture
    def adapter_with_graph(self):
        """Create adapter with validation graph."""
        adapter = PythonAdapterComplete()

        graph = ValidationGraph('my_func')
        node = ValidationNode('c1', 'test', ClauseSeverity.MANDATORY)
        graph.add_node(node)
        adapter.validation_graphs['my_func'] = graph

        return adapter

    def test_create_introspection_api(self, adapter_with_graph):
        """Test 1181: Create introspection API."""
        api = IntrospectionAPI(adapter_with_graph)
        assert api.adapter is adapter_with_graph
        assert api.query_engine is not None
        assert api.history_tracker is not None

    def test_set_metadata(self, adapter_with_graph):
        """Test 1182: Set contract metadata."""
        api = IntrospectionAPI(adapter_with_graph)
        metadata = ContractMetadata('test')
        api.set_metadata(metadata)

        assert api.metadata is metadata
        assert api.enricher.metadata is metadata

    def test_get_loaded_functions(self, adapter_with_graph):
        """Test 1183: Get loaded functions."""
        api = IntrospectionAPI(adapter_with_graph)
        functions = api.get_loaded_functions()

        assert 'my_func' in functions

    def test_get_function_info(self, adapter_with_graph):
        """Test 1184: Get function info."""
        api = IntrospectionAPI(adapter_with_graph)
        info = api.get_function_info('my_func')

        assert info is not None
        assert info['name'] == 'my_func'
        assert info['clauses'] == 1

    def test_get_function_info_missing(self, adapter_with_graph):
        """Test 1185: Get info for missing function."""
        api = IntrospectionAPI(adapter_with_graph)
        info = api.get_function_info('nonexistent')

        assert info is None

    def test_create_snapshot(self, adapter_with_graph):
        """Test 1186: Create state snapshot."""
        api = IntrospectionAPI(adapter_with_graph)
        snapshot = api.create_snapshot()

        assert isinstance(snapshot, StateSnapshot)
        assert 'my_func' in snapshot.loaded_functions
        assert snapshot.timestamp.endswith('Z')

    def test_snapshot_has_statistics(self, adapter_with_graph):
        """Test 1187: Snapshot has statistics."""
        api = IntrospectionAPI(adapter_with_graph)
        snapshot = api.create_snapshot()

        assert isinstance(snapshot.statistics, dict)

    def test_snapshot_has_configuration(self, adapter_with_graph):
        """Test 1188: Snapshot has configuration."""
        api = IntrospectionAPI(adapter_with_graph)
        snapshot = api.create_snapshot()

        assert isinstance(snapshot.configuration, dict)

    def test_query_passthrough(self, adapter_with_graph):
        """Test 1189: Query passthrough."""
        api = IntrospectionAPI(adapter_with_graph)
        result = api.query('contract.functions')

        assert 'my_func' in result

    def test_get_invocation_statistics_empty(self, adapter_with_graph):
        """Test 1190: Get empty invocation statistics."""
        api = IntrospectionAPI(adapter_with_graph)
        stats = api.get_invocation_statistics()

        assert stats['total'] == 0

    def test_get_invocation_statistics_with_data(self, adapter_with_graph):
        """Test 1191: Get invocation statistics with data."""
        api = IntrospectionAPI(adapter_with_graph)
        api.history_tracker.record_invocation('func1', True, 10.0)
        api.history_tracker.record_invocation('func2', False, 5.0)

        stats = api.get_invocation_statistics()
        assert stats['total'] == 2
        assert stats['successful'] == 1

    def test_get_recent_invocations(self, adapter_with_graph):
        """Test 1192: Get recent invocations."""
        api = IntrospectionAPI(adapter_with_graph)
        api.history_tracker.record_invocation('func1', True, 10.0)

        recent = api.get_recent_invocations(5)
        assert len(recent) == 1

    def test_get_recent_violations(self, adapter_with_graph):
        """Test 1193: Get recent violations."""
        api = IntrospectionAPI(adapter_with_graph)
        api.history_tracker.record_violation('func1', 'c1', 'msg')

        recent = api.get_recent_violations(5)
        assert len(recent) == 1
        assert recent[0]['clause_id'] == 'c1'

    def test_get_ownership_statistics(self, adapter_with_graph):
        """Test 1194: Get ownership statistics."""
        api = IntrospectionAPI(adapter_with_graph)
        stats = api.get_ownership_statistics()

        assert isinstance(stats, dict)

    def test_default_metadata_is_none(self, adapter_with_graph):
        """Test 1195: Default metadata is None."""
        api = IntrospectionAPI(adapter_with_graph)
        assert api.metadata is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
