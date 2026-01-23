"""
Paper decomposition using RLM to extract structured information.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from rlm import RLM


def decompose_paper(rlm_client: RLM, text_chunks: list[str]) -> dict:
    """
    Decompose a paper into structured JSON format using RLM.
    
    Args:
        rlm_client: RLM client instance
        text_chunks: List of text chunks from the paper
        
    Returns:
        Structured dictionary matching the decomposition schema
        
    Raises:
        ValueError: If RLM fails to produce valid JSON after retries
    """
    # Load the decomposition prompt
    prompt_path = Path(__file__).parent / "prompts" / "decompose_prompt.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    
    # Process each chunk and collect partial results
    partial_results = []
    
    for i, chunk in enumerate(text_chunks):
        print(f"Processing chunk {i+1}/{len(text_chunks)}...")
        
        # Construct the full prompt
        full_prompt = f"{prompt_template}\n\n---\n\nPaper text:\n\n{chunk}"
        
        # Call RLM with retry logic for invalid JSON
        max_retries = 3
        for attempt in range(max_retries):
            response = rlm_client(full_prompt)
            
            # Try to parse JSON
            try:
                result = _extract_json_from_response(response)
                partial_results.append(result)
                break
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # Ask RLM to fix the JSON
                    full_prompt = f"{prompt_template}\n\nYour previous response was not valid JSON. Please output ONLY valid JSON with no additional text.\n\nPaper text:\n\n{chunk}"
                else:
                    print(f"Skipping chunk {i+1} after {max_retries} failed attempts")
    
    if not partial_results:
        raise ValueError("Failed to extract any valid structured data from the paper")
    
    # Merge partial results
    merged = _merge_partial_results(partial_results)
    
    # Validate the final schema
    _validate_schema(merged)
    
    return merged


def _extract_json_from_response(response: str) -> dict:
    """
    Extract JSON from RLM response, handling potential markdown code blocks.
    
    Args:
        response: RLM response text
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        json.JSONDecodeError: If JSON parsing fails
    """
    # Try direct parsing first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try extracting from markdown code blocks
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        if end > start:
            json_str = response[start:end].strip()
            return json.loads(json_str)
    
    if "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        if end > start:
            json_str = response[start:end].strip()
            return json.loads(json_str)
    
    # Last resort: try to find JSON object boundaries
    start_idx = response.find("{")
    end_idx = response.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = response[start_idx:end_idx+1]
        return json.loads(json_str)
    
    # If all else fails, raise the original error
    return json.loads(response)


def _merge_partial_results(partial_results: list[dict]) -> dict:
    """
    Merge multiple partial paper decomposition results into one.
    
    Args:
        partial_results: List of partial decomposition dictionaries
        
    Returns:
        Merged dictionary
    """
    if len(partial_results) == 1:
        return partial_results[0]
    
    merged = {
        "title": None,
        "authors": [],
        "abstract": None,
        "sections": [],
        "experiments": [],
        "reproducibility_assessment": {
            "difficulty": "medium",
            "estimated_effort_hours": 0,
            "notes": ""
        }
    }
    
    # Take title and abstract from first non-null occurrence
    for result in partial_results:
        if merged["title"] is None and result.get("title"):
            merged["title"] = result["title"]
        if merged["abstract"] is None and result.get("abstract"):
            merged["abstract"] = result["abstract"]
        if not merged["authors"] and result.get("authors"):
            merged["authors"] = result["authors"]
    
    # Collect all sections (deduplicate by id)
    seen_section_ids = set()
    for result in partial_results:
        for section in result.get("sections", []):
            section_id = section.get("id", "")
            if section_id and section_id not in seen_section_ids:
                merged["sections"].append(section)
                seen_section_ids.add(section_id)
    
    # Collect all experiments (deduplicate by id, limit to 5)
    seen_experiment_ids = set()
    for result in partial_results:
        for experiment in result.get("experiments", []):
            experiment_id = experiment.get("id", "")
            if experiment_id and experiment_id not in seen_experiment_ids:
                if len(merged["experiments"]) < 5:
                    merged["experiments"].append(experiment)
                    seen_experiment_ids.add(experiment_id)
    
    # Use the most pessimistic reproducibility assessment
    difficulty_order = {"low": 0, "medium": 1, "high": 2}
    max_difficulty = "low"
    total_hours = 0
    notes_list = []
    
    for result in partial_results:
        if "reproducibility_assessment" in result:
            assessment = result["reproducibility_assessment"]
            difficulty = assessment.get("difficulty", "medium")
            if difficulty_order.get(difficulty, 1) > difficulty_order.get(max_difficulty, 0):
                max_difficulty = difficulty
            total_hours += assessment.get("estimated_effort_hours", 0)
            if assessment.get("notes"):
                notes_list.append(assessment["notes"])
    
    merged["reproducibility_assessment"] = {
        "difficulty": max_difficulty,
        "estimated_effort_hours": max(total_hours, 1),
        "notes": " | ".join(notes_list) if notes_list else ""
    }
    
    return merged


def _validate_schema(data: dict) -> None:
    """
    Validate that the decomposition result matches the expected schema.
    
    Args:
        data: Decomposition dictionary to validate
        
    Raises:
        ValueError: If schema validation fails
    """
    required_keys = ["title", "authors", "abstract", "sections", "experiments", "reproducibility_assessment"]
    
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")
    
    if not isinstance(data["authors"], list):
        raise ValueError("'authors' must be a list")
    
    if not isinstance(data["sections"], list):
        raise ValueError("'sections' must be a list")
    
    if not isinstance(data["experiments"], list):
        raise ValueError("'experiments' must be a list")
    
    # Validate experiment structure
    for i, exp in enumerate(data["experiments"]):
        if "id" not in exp:
            raise ValueError(f"Experiment {i} missing 'id' field")
        if "title" not in exp:
            raise ValueError(f"Experiment {i} missing 'title' field")
    
    # Validate reproducibility assessment
    assessment = data["reproducibility_assessment"]
    if "difficulty" not in assessment:
        raise ValueError("reproducibility_assessment missing 'difficulty'")
    if assessment["difficulty"] not in ["low", "medium", "high"]:
        raise ValueError(f"Invalid difficulty: {assessment['difficulty']}")
