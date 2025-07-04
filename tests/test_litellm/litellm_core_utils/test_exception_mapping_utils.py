import os
import sys

import pytest

sys.path.insert(
    0, os.path.abspath("../../..")
)  # Adds the parent directory to the system path

from litellm.litellm_core_utils.exception_mapping_utils import ExceptionCheckers

# Test cases for is_error_str_context_window_exceeded
# Tuple format: (error_message, expected_result)
context_window_test_cases = [
    # Positive cases (should return True)
    ("An error occurred: The input exceeds the model's maximum context limit of 8192 tokens.", True),
    ("Some text before, this model's maximum context length is 4096 tokens. Some text after.", True),
    ("Validation Error: string too long. expected a string with maximum length 1000.", True),
    ("Your prompt is longer than the model's context length of 2048.", True),
    ("AWS Bedrock Error: The request payload size has exceed context limit.", True),

    # Test case insensitivity
    ("ERROR: THIS MODEL'S MAXIMUM CONTEXT LENGTH IS 1024.", True),

    # Negative cases (should return False)
    ("A generic API error occurred.", False),
    ("Invalid API Key provided.", False),
    ("Rate limit reached for requests.", False),
    ("The context is large, but acceptable.", False),
    ("", False), # Empty string
]

@pytest.mark.parametrize("error_str, expected", context_window_test_cases)
def test_is_error_str_context_window_exceeded(error_str, expected):
    """
    Tests the is_error_str_context_window_exceeded function with various error strings.
    """
    assert ExceptionCheckers.is_error_str_context_window_exceeded(error_str) == expected

class TestExceptionCheckers:
    """Test the ExceptionCheckers utility methods"""

    def test_is_azure_content_policy_violation_error_with_policy_violation_text(self):
        """Test detection of Azure content policy violation with explicit policy violation text"""
        
        error_strings = [
            "invalid_request_error content_policy_violation occurred",
            "The response was filtered due to the prompt triggering Azure OpenAI's content management policy",
            "Your task failed as a result of our safety system detecting harmful content",
            "The model produced invalid content that violates our policy",
            "Request blocked due to content_filter_policy restrictions"
        ]
        
        for error_str in error_strings:
            result = ExceptionCheckers.is_azure_content_policy_violation_error(error_str)
            assert result is True, f"Should detect policy violation in: {error_str}"

    def test_is_azure_content_policy_violation_error_case_insensitive(self):
        """Test that content policy violation detection is case insensitive"""
        
        error_strings = [
            "INVALID_REQUEST_ERROR CONTENT_POLICY_VIOLATION",
            "The Response Was Filtered Due To The Prompt Triggering Azure OpenAI's Content Management",
            "YOUR TASK FAILED AS A RESULT OF OUR SAFETY SYSTEM",
            "Content_Filter_Policy restriction detected"
        ]
        
        for error_str in error_strings:
            result = ExceptionCheckers.is_azure_content_policy_violation_error(error_str)
            assert result is True, f"Should detect policy violation in uppercase: {error_str}"

    def test_is_azure_content_policy_violation_error_with_non_policy_errors(self):
        """Test that non-policy violation errors are not detected as policy violations"""
        
        error_strings = [
            "Invalid API key provided",
            "Rate limit exceeded for current model",
            "Model not found: gpt-nonexistent",
            "Request timeout occurred",
            "Authentication failed",
            "Insufficient quota remaining",
            "Bad request format",
            "Internal server error occurred"
        ]
        
        for error_str in error_strings:
            result = ExceptionCheckers.is_azure_content_policy_violation_error(error_str)
            assert result is False, f"Should NOT detect policy violation in: {error_str}"

    def test_is_azure_content_policy_violation_error_with_partial_matches(self):
        """Test that partial keyword matches work correctly"""
        
        # These should match because they contain the required substrings
        positive_cases = [
            "Error: content_policy_violation detected in request",
            "Safety content management, your task failed as a result of our safety system",
            "the model produced invalid content",
        ]
        
        for error_str in positive_cases:
            print("testing positive case=", error_str)
            result = ExceptionCheckers.is_azure_content_policy_violation_error(error_str)
            assert result is True, f"Should detect policy violation in: {error_str}"
        
        # These should not match even though they contain similar words
        negative_cases = [
            "Invalid content format in request",  # "invalid" but not "invalid content"
            "Policy configuration error",         # "policy" but not policy violation context
            "Content type not supported",         # "content" but not content filter context  
            "Management API unavailable"          # "management" but not content management context
        ]
        
        for error_str in negative_cases:
            result = ExceptionCheckers.is_azure_content_policy_violation_error(error_str)
            assert result is False, f"Should NOT detect policy violation in: {error_str}"
