"""
Unit tests for paper decomposition functionality.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from paper_decomposer.decompose import (
    decompose_paper,
    _extract_json_from_response,
    _merge_partial_results,
    _validate_schema
)


class TestDecompose(unittest.TestCase):
    """Test paper decomposition functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_paper_text = """
        Title: A Study on Synthetic Dataset Generation
        
        Authors: John Doe, Jane Smith
        
        Abstract: We investigate synthetic dataset generation for machine learning.
        
        1. Introduction
        Machine learning requires data...
        
        2. Experiment
        We train a logistic regression on synthetic data X~N(0,1).
        Results: accuracy 0.9, figure 1 shows scatter plot.
        """
        
        self.sample_decomposition = {
            "title": "A Study on Synthetic Dataset Generation",
            "authors": ["John Doe", "Jane Smith"],
            "abstract": "We investigate synthetic dataset generation for machine learning.",
            "sections": [
                {
                    "id": "sec1",
                    "heading": "Introduction",
                    "summary": "Overview of the problem"
                }
            ],
            "experiments": [
                {
                    "id": "exp1",
                    "title": "Logistic Regression Experiment",
                    "description": "Train logistic regression on synthetic data",
                    "dataset_info": {
                        "name": "Synthetic",
                        "source": "Generated",
                        "size": "1000 samples",
                        "is_synthetic": True
                    },
                    "inputs": "X~N(0,1)",
                    "outputs": "Binary classification",
                    "model_spec": {
                        "type": "logistic_regression",
                        "architecture": None,
                        "framework": "sklearn"
                    },
                    "hyperparameters": {
                        "learning_rate": None,
                        "batch_size": None,
                        "epochs": None,
                        "other": {}
                    },
                    "metrics_reported": ["accuracy"],
                    "key_figures": ["figure_1"]
                }
            ],
            "reproducibility_assessment": {
                "difficulty": "low",
                "estimated_effort_hours": 2,
                "notes": "Simple experiment"
            }
        }
    
    def test_extract_json_from_response_direct(self):
        """Test extracting JSON from a direct JSON response."""
        json_str = json.dumps(self.sample_decomposition)
        result = _extract_json_from_response(json_str)
        self.assertEqual(result["title"], self.sample_decomposition["title"])
    
    def test_extract_json_from_response_markdown(self):
        """Test extracting JSON from markdown code blocks."""
        json_str = json.dumps(self.sample_decomposition)
        response = f"Here is the result:\n```json\n{json_str}\n```\nEnd"
        result = _extract_json_from_response(response)
        self.assertEqual(result["title"], self.sample_decomposition["title"])
    
    def test_extract_json_from_response_generic_codeblock(self):
        """Test extracting JSON from generic code blocks."""
        json_str = json.dumps(self.sample_decomposition)
        response = f"Result:\n```\n{json_str}\n```"
        result = _extract_json_from_response(response)
        self.assertEqual(result["title"], self.sample_decomposition["title"])
    
    def test_validate_schema_valid(self):
        """Test schema validation with valid data."""
        # Should not raise
        _validate_schema(self.sample_decomposition)
    
    def test_validate_schema_missing_key(self):
        """Test schema validation with missing required key."""
        invalid_data = self.sample_decomposition.copy()
        del invalid_data["title"]
        
        with self.assertRaises(ValueError) as cm:
            _validate_schema(invalid_data)
        self.assertIn("title", str(cm.exception))
    
    def test_validate_schema_invalid_difficulty(self):
        """Test schema validation with invalid difficulty."""
        invalid_data = self.sample_decomposition.copy()
        invalid_data["reproducibility_assessment"]["difficulty"] = "invalid"
        
        with self.assertRaises(ValueError) as cm:
            _validate_schema(invalid_data)
        self.assertIn("difficulty", str(cm.exception))
    
    def test_merge_partial_results_single(self):
        """Test merging with single result."""
        result = _merge_partial_results([self.sample_decomposition])
        self.assertEqual(result["title"], self.sample_decomposition["title"])
    
    def test_merge_partial_results_multiple(self):
        """Test merging multiple partial results."""
        partial1 = {
            "title": "Test Paper",
            "authors": ["Author 1"],
            "abstract": "Abstract here",
            "sections": [{"id": "s1", "heading": "Intro", "summary": "..."}],
            "experiments": [{"id": "e1", "title": "Exp1", "description": "..."}],
            "reproducibility_assessment": {"difficulty": "low", "estimated_effort_hours": 1, "notes": ""}
        }
        
        partial2 = {
            "title": None,
            "authors": [],
            "abstract": None,
            "sections": [{"id": "s2", "heading": "Methods", "summary": "..."}],
            "experiments": [{"id": "e2", "title": "Exp2", "description": "..."}],
            "reproducibility_assessment": {"difficulty": "high", "estimated_effort_hours": 3, "notes": "Complex"}
        }
        
        merged = _merge_partial_results([partial1, partial2])
        
        # Should take title from first
        self.assertEqual(merged["title"], "Test Paper")
        
        # Should combine sections
        self.assertEqual(len(merged["sections"]), 2)
        
        # Should combine experiments
        self.assertEqual(len(merged["experiments"]), 2)
        
        # Should use most pessimistic difficulty
        self.assertEqual(merged["reproducibility_assessment"]["difficulty"], "high")
    
    @patch('paper_decomposer.decompose.RLM')
    def test_decompose_paper_success(self, mock_rlm_class):
        """Test successful paper decomposition."""
        # Setup mock
        mock_rlm = Mock()
        mock_rlm_class.return_value = mock_rlm
        
        # Mock RLM response
        mock_rlm.return_value = json.dumps(self.sample_decomposition)
        
        # Run decomposition
        result = decompose_paper(mock_rlm, [self.sample_paper_text])
        
        # Verify
        self.assertEqual(result["title"], self.sample_decomposition["title"])
        self.assertEqual(len(result["experiments"]), 1)
        self.assertEqual(result["experiments"][0]["id"], "exp1")
    
    @patch('paper_decomposer.decompose.RLM')
    def test_decompose_paper_multiple_chunks(self, mock_rlm_class):
        """Test decomposition with multiple text chunks."""
        mock_rlm = Mock()
        
        # Return different partial results for each chunk
        responses = [
            json.dumps({
                "title": "Test",
                "authors": ["A"],
                "abstract": "Abs",
                "sections": [{"id": "s1", "heading": "H1", "summary": "S1"}],
                "experiments": [{"id": "e1", "title": "E1", "description": "D1"}],
                "reproducibility_assessment": {"difficulty": "low", "estimated_effort_hours": 1, "notes": ""}
            }),
            json.dumps({
                "title": None,
                "authors": [],
                "abstract": None,
                "sections": [{"id": "s2", "heading": "H2", "summary": "S2"}],
                "experiments": [{"id": "e2", "title": "E2", "description": "D2"}],
                "reproducibility_assessment": {"difficulty": "medium", "estimated_effort_hours": 2, "notes": ""}
            })
        ]
        
        mock_rlm.side_effect = responses
        
        result = decompose_paper(mock_rlm, ["chunk1", "chunk2"])
        
        # Should have merged results
        self.assertEqual(len(result["sections"]), 2)
        self.assertEqual(len(result["experiments"]), 2)
        self.assertEqual(mock_rlm.call_count, 2)


class TestJSONExtraction(unittest.TestCase):
    """Test JSON extraction edge cases."""
    
    def test_extract_with_text_before_and_after(self):
        """Test extraction when JSON is embedded in text."""
        data = {"key": "value", "number": 42}
        response = f"Some preamble text\n{json.dumps(data)}\nSome trailing text"
        
        result = _extract_json_from_response(response)
        self.assertEqual(result["key"], "value")
    
    def test_extract_with_nested_braces(self):
        """Test extraction with nested JSON objects."""
        data = {
            "outer": {
                "inner": {
                    "deep": "value"
                }
            }
        }
        result = _extract_json_from_response(json.dumps(data))
        self.assertEqual(result["outer"]["inner"]["deep"], "value")


if __name__ == "__main__":
    unittest.main()
