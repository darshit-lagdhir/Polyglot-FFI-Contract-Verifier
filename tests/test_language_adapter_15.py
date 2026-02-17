"""Test Suite for Language Adapter - Prompt 15/25: 85 tests."""

import pytest
from modules.module_08_language_adapter import (
    APIDocGenerator,
    ContractDocGenerator,
    TutorialGenerator,
    HelpSystem,
    ReportFormatter,
    DocumentationManager,
    PythonAdapterComplete,
    ContractMetadata,
    StateSnapshot,
)


# ════════════════════════════════════════════════════════════════════════════
# API DOC GENERATOR TESTS (20 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestAPIDocGenerator:
    """APIDocGenerator tests (20 tests)."""

    def test_create_doc_generator(self):
        """Test 1291: Create API doc generator."""
        gen = APIDocGenerator()
        assert len(gen.sections) == 0

    def test_document_class_name(self):
        """Test 1292: Document class extracts name."""
        class SampleClass:
            """Sample docstring."""
            def method_a(self):
                """Method A."""
                pass

        gen = APIDocGenerator()
        doc = gen.document_class(SampleClass)

        assert doc['name'] == 'SampleClass'

    def test_document_class_docstring(self):
        """Test 1293: Document class extracts docstring."""
        class SampleClass:
            """Sample docstring."""
            pass

        gen = APIDocGenerator()
        doc = gen.document_class(SampleClass)

        assert 'Sample docstring' in doc['docstring']

    def test_document_class_empty_docstring(self):
        """Test 1294: Class without docstring."""
        class NoDoc:
            pass

        gen = APIDocGenerator()
        doc = gen.document_class(NoDoc)

        assert doc['docstring'] == ''

    def test_document_public_methods(self):
        """Test 1295: Document public methods only."""
        class TestClass:
            def public_method(self):
                """Public."""
                pass

            def _private_method(self):
                """Private."""
                pass

        gen = APIDocGenerator()
        doc = gen.document_class(TestClass)

        method_names = [m['name'] for m in doc['methods']]
        assert 'public_method' in method_names
        assert '_private_method' not in method_names

    def test_document_method_name(self):
        """Test 1296: Document method extracts name."""
        def sample_func():
            """Sample."""
            pass

        gen = APIDocGenerator()
        doc = gen.document_method('sample_func', sample_func)

        assert doc['name'] == 'sample_func'

    def test_document_method_docstring(self):
        """Test 1297: Document method extracts docstring."""
        def sample_func():
            """Sample function docstring."""
            pass

        gen = APIDocGenerator()
        doc = gen.document_method('sample_func', sample_func)

        assert 'Sample function docstring' in doc['docstring']

    def test_document_method_signature(self):
        """Test 1298: Document method extracts signature."""
        def sample_func(x: int, y: str) -> bool:
            """Has signature."""
            pass

        gen = APIDocGenerator()
        doc = gen.document_method('sample_func', sample_func)

        assert 'x' in doc['signature']
        assert 'y' in doc['signature']

    def test_document_method_no_docstring(self):
        """Test 1299: Method without docstring."""
        def no_doc():
            pass

        gen = APIDocGenerator()
        doc = gen.document_method('no_doc', no_doc)

        assert doc['docstring'] == ''

    def test_format_markdown_header(self):
        """Test 1300: Markdown contains class header."""
        class TestClass:
            """Test class."""
            pass

        gen = APIDocGenerator()
        doc = gen.document_class(TestClass)
        md = gen.format_markdown(doc)

        assert '## TestClass' in md

    def test_format_markdown_docstring(self):
        """Test 1301: Markdown contains class docstring."""
        class TestClass:
            """A great class."""
            pass

        gen = APIDocGenerator()
        doc = gen.document_class(TestClass)
        md = gen.format_markdown(doc)

        assert 'A great class' in md

    def test_format_markdown_methods_header(self):
        """Test 1302: Markdown contains methods header."""
        class TestClass:
            def do_something(self):
                """Does stuff."""
                pass

        gen = APIDocGenerator()
        doc = gen.document_class(TestClass)
        md = gen.format_markdown(doc)

        assert '### Methods' in md

    def test_format_markdown_method_name(self):
        """Test 1303: Markdown contains method name."""
        class TestClass:
            def do_something(self):
                """Does it."""
                pass

        gen = APIDocGenerator()
        doc = gen.document_class(TestClass)
        md = gen.format_markdown(doc)

        assert 'do_something' in md

    def test_format_markdown_no_methods(self):
        """Test 1304: Markdown when no public methods."""
        class EmptyClass:
            """Empty."""
            pass

        gen = APIDocGenerator()
        doc = gen.document_class(EmptyClass)
        md = gen.format_markdown(doc)

        assert '## EmptyClass' in md

    def test_document_multiple_methods(self):
        """Test 1305: Multiple methods documented."""
        class Multi:
            def method_a(self):
                """A."""
                pass
            def method_b(self):
                """B."""
                pass

        gen = APIDocGenerator()
        doc = gen.document_class(Multi)

        method_names = [m['name'] for m in doc['methods']]
        assert 'method_a' in method_names
        assert 'method_b' in method_names

    def test_document_real_class(self):
        """Test 1306: Document a real adapter class."""
        gen = APIDocGenerator()
        doc = gen.document_class(APIDocGenerator)

        assert doc['name'] == 'APIDocGenerator'
        method_names = [m['name'] for m in doc['methods']]
        assert 'document_class' in method_names

    def test_format_markdown_method_docstring(self):
        """Test 1307: Markdown includes method docstring."""
        class TestClass:
            def compute(self):
                """Computes the value."""
                pass

        gen = APIDocGenerator()
        doc = gen.document_class(TestClass)
        md = gen.format_markdown(doc)

        assert 'Computes the value' in md

    def test_sections_initially_empty(self):
        """Test 1308: Sections list is empty initially."""
        gen = APIDocGenerator()
        assert gen.sections == []

    def test_document_class_returns_dict(self):
        """Test 1309: document_class returns dict."""
        class X:
            pass

        gen = APIDocGenerator()
        doc = gen.document_class(X)

        assert isinstance(doc, dict)
        assert 'name' in doc
        assert 'docstring' in doc
        assert 'methods' in doc

    def test_format_markdown_returns_str(self):
        """Test 1310: format_markdown returns str."""
        gen = APIDocGenerator()
        doc = {'name': 'X', 'docstring': '', 'methods': []}
        md = gen.format_markdown(doc)

        assert isinstance(md, str)


# ════════════════════════════════════════════════════════════════════════════
# CONTRACT DOC GENERATOR TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestContractDocGenerator:
    """ContractDocGenerator tests (15 tests)."""

    def test_create_contract_doc_generator(self):
        """Test 1311: Create contract doc generator."""
        gen = ContractDocGenerator()
        assert gen.metadata is None

    def test_set_metadata(self):
        """Test 1312: Set contract metadata."""
        gen = ContractDocGenerator()
        metadata = ContractMetadata('test')
        gen.set_metadata(metadata)

        assert gen.metadata is metadata

    def test_document_contract_id(self):
        """Test 1313: Document contract extracts ID."""
        contract = {
            'contract_id': 'test_contract',
            'schema_version': '1.0.0',
            'functions': {}
        }

        gen = ContractDocGenerator()
        doc = gen.document_contract(contract)

        assert doc['contract_id'] == 'test_contract'

    def test_document_contract_version(self):
        """Test 1314: Document contract extracts version."""
        contract = {
            'contract_id': 'test',
            'schema_version': '2.0.0',
            'functions': {}
        }

        gen = ContractDocGenerator()
        doc = gen.document_contract(contract)

        assert doc['version'] == '2.0.0'

    def test_document_contract_functions(self):
        """Test 1315: Document contract with functions."""
        contract = {
            'contract_id': 'test',
            'schema_version': '1.0.0',
            'functions': {
                'func_a': {'parameters': []},
                'func_b': {'parameters': []}
            }
        }

        gen = ContractDocGenerator()
        doc = gen.document_contract(contract)

        assert len(doc['functions']) == 2

    def test_document_function_name(self):
        """Test 1316: Document function extracts name."""
        gen = ContractDocGenerator()
        doc = gen.document_function('my_func', {'parameters': []})

        assert doc['name'] == 'my_func'

    def test_document_function_parameters(self):
        """Test 1317: Document function extracts params."""
        func_contract = {
            'parameters': [
                {'name': 'x', 'type': 'int', 'clauses': []},
                {'name': 'y', 'type': 'float', 'clauses': []}
            ]
        }

        gen = ContractDocGenerator()
        doc = gen.document_function('func', func_contract)

        assert len(doc['parameters']) == 2
        assert doc['parameters'][0]['name'] == 'x'
        assert doc['parameters'][1]['type'] == 'float'

    def test_document_function_with_clauses(self):
        """Test 1318: Document function with clause types."""
        func_contract = {
            'parameters': [
                {
                    'name': 'buf',
                    'type': 'pointer',
                    'clauses': [
                        {'clause_type': 'non_null'},
                        {'clause_type': 'size'}
                    ]
                }
            ]
        }

        gen = ContractDocGenerator()
        doc = gen.document_function('func', func_contract)

        assert 'non_null' in doc['parameters'][0]['clauses']
        assert 'size' in doc['parameters'][0]['clauses']

    def test_format_contract_markdown_header(self):
        """Test 1319: Contract markdown has header."""
        doc = {
            'contract_id': 'my_contract',
            'version': '1.0.0',
            'functions': []
        }

        gen = ContractDocGenerator()
        md = gen.format_markdown(doc)

        assert '# Contract: my_contract' in md

    def test_format_contract_markdown_version(self):
        """Test 1320: Contract markdown has version."""
        doc = {
            'contract_id': 'test',
            'version': '3.0.0',
            'functions': []
        }

        gen = ContractDocGenerator()
        md = gen.format_markdown(doc)

        assert '3.0.0' in md

    def test_format_contract_markdown_functions(self):
        """Test 1321: Contract markdown includes functions."""
        doc = {
            'contract_id': 'test',
            'version': '1.0',
            'functions': [
                {
                    'name': 'process_data',
                    'parameters': [
                        {'name': 'buf', 'type': 'pointer'}
                    ]
                }
            ]
        }

        gen = ContractDocGenerator()
        md = gen.format_markdown(doc)

        assert 'process_data' in md
        assert '`buf`' in md

    def test_document_empty_contract(self):
        """Test 1322: Document contract with no functions."""
        contract = {
            'contract_id': 'empty',
            'schema_version': '1.0',
            'functions': {}
        }

        gen = ContractDocGenerator()
        doc = gen.document_contract(contract)

        assert doc['functions'] == []

    def test_document_contract_missing_id(self):
        """Test 1323: Missing contract_id defaults."""
        gen = ContractDocGenerator()
        doc = gen.document_contract({})

        assert doc['contract_id'] == 'unknown'

    def test_document_contract_missing_version(self):
        """Test 1324: Missing version defaults."""
        gen = ContractDocGenerator()
        doc = gen.document_contract({})

        assert doc['version'] == 'unknown'

    def test_format_markdown_with_description(self):
        """Test 1325: Markdown includes function description."""
        doc = {
            'contract_id': 'test',
            'version': '1.0',
            'functions': [
                {
                    'name': 'func',
                    'description': 'Does something important',
                    'parameters': []
                }
            ]
        }

        gen = ContractDocGenerator()
        md = gen.format_markdown(doc)

        assert 'Does something important' in md


# ════════════════════════════════════════════════════════════════════════════
# TUTORIAL GENERATOR TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestTutorialGenerator:
    """TutorialGenerator tests (15 tests)."""

    def test_create_tutorial_generator(self):
        """Test 1326: Create tutorial generator."""
        gen = TutorialGenerator()
        assert len(gen.examples) == 0

    def test_add_example(self):
        """Test 1327: Add example."""
        gen = TutorialGenerator()
        gen.add_example('Test', 'code', 'explanation', ['tag1'])

        assert len(gen.examples) == 1

    def test_add_example_stores_title(self):
        """Test 1328: Example stores title."""
        gen = TutorialGenerator()
        gen.add_example('My Title', 'code', 'expl', [])

        assert gen.examples[0]['title'] == 'My Title'

    def test_add_example_stores_code(self):
        """Test 1329: Example stores code."""
        gen = TutorialGenerator()
        gen.add_example('T', 'print("hi")', 'expl', [])

        assert gen.examples[0]['code'] == 'print("hi")'

    def test_add_example_stores_explanation(self):
        """Test 1330: Example stores explanation."""
        gen = TutorialGenerator()
        gen.add_example('T', 'code', 'My explanation.', [])

        assert gen.examples[0]['explanation'] == 'My explanation.'

    def test_add_example_stores_tags(self):
        """Test 1331: Example stores tags."""
        gen = TutorialGenerator()
        gen.add_example('T', 'c', 'e', ['basic', 'intro'])

        assert gen.examples[0]['tags'] == ['basic', 'intro']

    def test_add_example_default_tags(self):
        """Test 1332: Default tags are empty list."""
        gen = TutorialGenerator()
        gen.add_example('T', 'c', 'e')

        assert gen.examples[0]['tags'] == []

    def test_generate_tutorial_header(self):
        """Test 1333: Tutorial has header."""
        gen = TutorialGenerator()
        gen.add_example('E1', 'code', 'explain', ['basics'])

        tutorial = gen.generate_tutorial('basics')

        assert '# Tutorial: basics' in tutorial

    def test_generate_tutorial_includes_title(self):
        """Test 1334: Tutorial includes example title."""
        gen = TutorialGenerator()
        gen.add_example('Setup Guide', 'code', 'expl', ['setup'])

        tutorial = gen.generate_tutorial('setup')

        assert 'Setup Guide' in tutorial

    def test_generate_tutorial_includes_code(self):
        """Test 1335: Tutorial includes code block."""
        gen = TutorialGenerator()
        gen.add_example('T', 'x = 42', 'expl', ['demo'])

        tutorial = gen.generate_tutorial('demo')

        assert 'x = 42' in tutorial
        assert '```python' in tutorial

    def test_generate_tutorial_includes_explanation(self):
        """Test 1336: Tutorial includes explanation."""
        gen = TutorialGenerator()
        gen.add_example('T', 'code', 'Important note here', ['n'])

        tutorial = gen.generate_tutorial('n')

        assert 'Important note here' in tutorial

    def test_generate_tutorial_tag_filtering(self):
        """Test 1337: Tutorial filters by tag."""
        gen = TutorialGenerator()
        gen.add_example('Basic', 'a', 'e1', ['basic'])
        gen.add_example('Advanced', 'b', 'e2', ['advanced'])

        tutorial = gen.generate_tutorial('basic')

        assert 'Basic' in tutorial
        assert 'Advanced' not in tutorial

    def test_generate_tutorial_no_tag_match(self):
        """Test 1338: No tag match uses all examples."""
        gen = TutorialGenerator()
        gen.add_example('E1', 'a', 'e1', ['tag1'])
        gen.add_example('E2', 'b', 'e2', ['tag2'])

        tutorial = gen.generate_tutorial('nonexistent')

        assert 'E1' in tutorial
        assert 'E2' in tutorial

    def test_generate_tutorial_numbering(self):
        """Test 1339: Examples are numbered."""
        gen = TutorialGenerator()
        gen.add_example('One', 'a', 'e1', ['t'])
        gen.add_example('Two', 'b', 'e2', ['t'])

        tutorial = gen.generate_tutorial('t')

        assert 'Example 1' in tutorial
        assert 'Example 2' in tutorial

    def test_generate_tutorial_empty(self):
        """Test 1340: Tutorial with no examples."""
        gen = TutorialGenerator()
        tutorial = gen.generate_tutorial('empty')

        assert '# Tutorial: empty' in tutorial


# ════════════════════════════════════════════════════════════════════════════
# HELP SYSTEM TESTS (15 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestHelpSystem:
    """HelpSystem tests (15 tests)."""

    def test_create_help_system(self):
        """Test 1341: Create help system."""
        hs = HelpSystem()
        assert len(hs.help_topics) > 0

    def test_default_topics_exist(self):
        """Test 1342: Default topics exist."""
        hs = HelpSystem()
        topics = hs.list_topics()

        assert 'quickstart' in topics
        assert 'caching' in topics
        assert 'diagnostics' in topics

    def test_get_help_exact_match(self):
        """Test 1343: Get help with exact match."""
        hs = HelpSystem()
        help_text = hs.get_help('quickstart')

        assert 'Quick Start' in help_text

    def test_get_help_caching(self):
        """Test 1344: Get help for caching."""
        hs = HelpSystem()
        help_text = hs.get_help('caching')

        assert 'Caching' in help_text

    def test_get_help_diagnostics(self):
        """Test 1345: Get help for diagnostics."""
        hs = HelpSystem()
        help_text = hs.get_help('diagnostics')

        assert 'Diagnostic' in help_text

    def test_get_help_partial_match(self):
        """Test 1346: Get help with partial match."""
        hs = HelpSystem()
        help_text = hs.get_help('cach')

        assert 'Caching' in help_text

    def test_get_help_no_match(self):
        """Test 1347: No help match returns suggestion."""
        hs = HelpSystem()
        help_text = hs.get_help('xyznonexistent')

        assert 'No help available' in help_text
        assert 'Available topics' in help_text

    def test_list_topics(self):
        """Test 1348: List topics."""
        hs = HelpSystem()
        topics = hs.list_topics()

        assert isinstance(topics, list)
        assert len(topics) >= 3

    def test_add_topic(self):
        """Test 1349: Add custom topic."""
        hs = HelpSystem()
        hs.add_topic('custom_topic', 'Custom help.')

        assert 'custom_topic' in hs.list_topics()

    def test_get_added_topic(self):
        """Test 1350: Get custom topic help."""
        hs = HelpSystem()
        hs.add_topic('my_topic', 'My custom help text.')

        assert hs.get_help('my_topic') == 'My custom help text.'

    def test_overwrite_topic(self):
        """Test 1351: Overwrite existing topic."""
        hs = HelpSystem()
        hs.add_topic('quickstart', 'New quickstart.')

        assert hs.get_help('quickstart') == 'New quickstart.'

    def test_no_match_lists_all_topics(self):
        """Test 1352: No match lists all available topics."""
        hs = HelpSystem()
        help_text = hs.get_help('zzz_no_match')

        for topic in hs.list_topics():
            assert topic in help_text

    def test_help_returns_string(self):
        """Test 1353: Help always returns string."""
        hs = HelpSystem()

        assert isinstance(hs.get_help('quickstart'), str)
        assert isinstance(hs.get_help('nonexistent'), str)

    def test_multiple_custom_topics(self):
        """Test 1354: Multiple custom topics."""
        hs = HelpSystem()
        hs.add_topic('topic_a', 'Content A')
        hs.add_topic('topic_b', 'Content B')

        assert hs.get_help('topic_a') == 'Content A'
        assert hs.get_help('topic_b') == 'Content B'

    def test_quickstart_mentions_adapter(self):
        """Test 1355: Quickstart mentions adapter creation."""
        hs = HelpSystem()
        help_text = hs.get_help('quickstart')

        assert 'PythonAdapterComplete' in help_text


# ════════════════════════════════════════════════════════════════════════════
# REPORT FORMATTER TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestReportFormatter:
    """ReportFormatter tests (10 tests)."""

    def test_create_report_formatter(self):
        """Test 1356: Create report formatter."""
        formatter = ReportFormatter()
        assert formatter is not None

    def test_format_performance_report_header(self):
        """Test 1357: Performance report has header."""
        formatter = ReportFormatter()
        report = formatter.format_performance_report({})

        assert 'PERFORMANCE REPORT' in report

    def test_format_performance_report_time(self):
        """Test 1358: Performance report shows total time."""
        metrics = {'total_time_ms': 125.5}

        formatter = ReportFormatter()
        report = formatter.format_performance_report(metrics)

        assert '125.50' in report

    def test_format_performance_report_breakdown(self):
        """Test 1359: Performance report shows breakdown."""
        metrics = {
            'timing_breakdown': {
                'normalization': 10.0,
                'validation': 100.0
            }
        }

        formatter = ReportFormatter()
        report = formatter.format_performance_report(metrics)

        assert 'normalization' in report
        assert '10.00' in report

    def test_format_performance_report_memory(self):
        """Test 1360: Performance report shows memory."""
        metrics = {
            'memory_stats': {
                'active_wrappers': 5,
                'pinned_buffers': 3
            }
        }

        formatter = ReportFormatter()
        report = formatter.format_performance_report(metrics)

        assert 'Active Wrappers: 5' in report
        assert 'Pinned Buffers: 3' in report

    def test_format_health_report_header(self):
        """Test 1361: Health report has header."""
        snapshot = StateSnapshot(
            timestamp='2024-01-01T00:00:00Z'
        )

        formatter = ReportFormatter()
        report = formatter.format_health_report(snapshot)

        assert 'SYSTEM HEALTH REPORT' in report

    def test_format_health_report_timestamp(self):
        """Test 1362: Health report shows timestamp."""
        snapshot = StateSnapshot(
            timestamp='2024-06-15T12:00:00Z'
        )

        formatter = ReportFormatter()
        report = formatter.format_health_report(snapshot)

        assert '2024-06-15' in report

    def test_format_health_report_functions(self):
        """Test 1363: Health report shows function count."""
        snapshot = StateSnapshot(
            timestamp='2024-01-01T00:00:00Z',
            loaded_functions=['func1', 'func2', 'func3']
        )

        formatter = ReportFormatter()
        report = formatter.format_health_report(snapshot)

        assert 'Loaded Functions: 3' in report

    def test_format_configuration_report_header(self):
        """Test 1364: Configuration report has header."""
        formatter = ReportFormatter()
        report = formatter.format_configuration_report({})

        assert 'CONFIGURATION REPORT' in report

    def test_format_configuration_report_content(self):
        """Test 1365: Configuration report shows content."""
        config = {
            'mode': 'strict',
            'caching': True,
            'nested': {
                'inner_key': 'inner_value'
            }
        }

        formatter = ReportFormatter()
        report = formatter.format_configuration_report(config)

        assert 'mode: strict' in report
        assert 'caching: True' in report
        assert 'inner_key: inner_value' in report


# ════════════════════════════════════════════════════════════════════════════
# DOCUMENTATION MANAGER TESTS (10 tests)
# ════════════════════════════════════════════════════════════════════════════

class TestDocumentationManager:
    """DocumentationManager tests (10 tests)."""

    def test_create_documentation_manager(self):
        """Test 1366: Create documentation manager."""
        adapter = PythonAdapterComplete()
        doc_mgr = DocumentationManager(adapter)

        assert doc_mgr.adapter is adapter

    def test_manager_has_api_doc_gen(self):
        """Test 1367: Manager has API doc generator."""
        adapter = PythonAdapterComplete()
        doc_mgr = DocumentationManager(adapter)

        assert isinstance(doc_mgr.api_doc_gen, APIDocGenerator)

    def test_manager_has_contract_doc_gen(self):
        """Test 1368: Manager has contract doc generator."""
        adapter = PythonAdapterComplete()
        doc_mgr = DocumentationManager(adapter)

        assert isinstance(
            doc_mgr.contract_doc_gen, ContractDocGenerator
        )

    def test_manager_has_tutorial_gen(self):
        """Test 1369: Manager has tutorial generator."""
        adapter = PythonAdapterComplete()
        doc_mgr = DocumentationManager(adapter)

        assert isinstance(doc_mgr.tutorial_gen, TutorialGenerator)

    def test_manager_has_help_system(self):
        """Test 1370: Manager has help system."""
        adapter = PythonAdapterComplete()
        doc_mgr = DocumentationManager(adapter)

        assert isinstance(doc_mgr.help_system, HelpSystem)

    def test_default_tutorials_loaded(self):
        """Test 1371: Default tutorials are loaded."""
        adapter = PythonAdapterComplete()
        doc_mgr = DocumentationManager(adapter)

        assert len(doc_mgr.tutorial_gen.examples) >= 2

    def test_manager_get_help(self):
        """Test 1372: Get help through manager."""
        adapter = PythonAdapterComplete()
        doc_mgr = DocumentationManager(adapter)

        help_text = doc_mgr.get_help('quickstart')
        assert 'Quick Start' in help_text

    def test_manager_generate_tutorial(self):
        """Test 1373: Generate tutorial through manager."""
        adapter = PythonAdapterComplete()
        doc_mgr = DocumentationManager(adapter)

        tutorial = doc_mgr.generate_tutorial('quickstart')
        assert 'Tutorial' in tutorial

    def test_manager_generate_contract_docs(self):
        """Test 1374: Generate contract docs through manager."""
        adapter = PythonAdapterComplete()
        doc_mgr = DocumentationManager(adapter)

        contract = {
            'contract_id': 'my_contract',
            'schema_version': '1.0.0',
            'functions': {}
        }

        docs = doc_mgr.generate_contract_docs(contract)
        assert 'Contract: my_contract' in docs

    def test_manager_generate_api_docs(self):
        """Test 1375: Generate API docs through manager."""
        adapter = PythonAdapterComplete()
        doc_mgr = DocumentationManager(adapter)

        docs = doc_mgr.generate_api_docs([APIDocGenerator])
        assert 'APIDocGenerator' in docs


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
