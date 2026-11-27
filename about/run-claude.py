#!/usr/bin/env python3
"""
Generate HTML files from build instructions using Claude API.

Usage:
    python run-claude.py build_instructions.txt index.html [--model MODEL] [--effort LEVEL]

The default model (Claude Opus 5.5) builds the About and Demo pages; mk-custom passes
--model claude-fable-5-2 for a custom game when CLAUDE_MODEL is set. The answer is streamed
with room for a whole game page; a page cut off by the token limit is an error, never written.
"""

import argparse
import sys
import os
from anthropic import Anthropic

MODEL = "claude-opus-5-5"
MAX_TOKENS = 128000


def read_file(filepath):
    """Read content from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def write_file(filepath, content):
    """Write content to a file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully generated: {filepath}")
    except Exception as e:
        print(f"Error writing file {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def calculate_cost(input_tokens, output_tokens, model=MODEL):
    """
    Calculate the cost of the API call.
    
    Pricing per million tokens:
    - Claude Opus 5.5: $4.00 input / $20.00 output
    - Claude Fable 5.2: $8.00 input / $40.00 output
    """
    # Pricing per million tokens
    pricing = {
        "claude-opus-5-5": {
            "input": 4.00,
            "output": 20.00
        },
        "claude-fable-5-2": {
            "input": 8.00,
            "output": 40.00
        }
    }
    
    if model not in pricing:
        print(f"Warning: no price known for {model}; cost shown at Fable 5.2 rates", file=sys.stderr)
    rates = pricing.get(model, pricing["claude-fable-5-2"])
    
    input_cost = (input_tokens / 1_000_000) * rates["input"]
    output_cost = (output_tokens / 1_000_000) * rates["output"]
    total_cost = input_cost + output_cost
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }


def generate_html(build_instructions, api_key=None, model=MODEL, effort=None):
    """
    Generate HTML from build instructions using Claude API.
    
    Args:
        build_instructions: The build instructions text
        api_key: Optional API key (if not set, uses ANTHROPIC_API_KEY env var)
    
    Returns:
        Tuple of (generated HTML content, cost information dict)
    """
    client = Anthropic(api_key=api_key)
    
    prompt = f"""Build a web page using the attached build instructions.

Build Instructions:
{build_instructions}

Please generate a complete, standalone HTML file following these instructions exactly. 
Do not include any explanatory text, commentary, or markdown code blocks - output only the raw HTML file content."""
    
    print(f"Generating HTML with Claude API ({model}, effort {effort or 'default'})...", file=sys.stderr)
    extra = {"fallbacks": "default"}
    if effort:
        extra["output_config"] = {"effort": effort}
    
    try:
        # Streamed, so a long answer (a whole game page plus thinking) never hits an
        # HTTP timeout; on a policy decline the API reruns the request on a fallback model.
        with client.beta.messages.stream(
            model=model,
            max_tokens=MAX_TOKENS,
            betas=["server-side-fallback-2026-07-01"],
            extra_body=extra,
            messages=[
                {"role": "user", "content": prompt}
            ]
        ) as stream:
            message = stream.get_final_message()
        
        if message.stop_reason == "refusal":
            print("Error: Claude declined the request", file=sys.stderr)
            sys.exit(1)
        if message.stop_reason == "max_tokens":
            print(f"Error: the answer was cut off at {MAX_TOKENS} tokens; nothing written", file=sys.stderr)
            sys.exit(1)
        if message.model != model:
            print(f"Note: answered by {message.model} (fallback)", file=sys.stderr)
        
        # Calculate cost
        cost_info = calculate_cost(
            message.usage.input_tokens,
            message.usage.output_tokens,
            message.model
        )
        
        # Extract text content from response
        html_content = ""
        for block in message.content:
            if block.type == "text":
                html_content += block.text
        
        # Clean up any markdown code blocks if present
        html_content = html_content.strip()
        if html_content.startswith("```html"):
            html_content = html_content[7:]  # Remove ```html
        if html_content.startswith("```"):
            html_content = html_content[3:]  # Remove ```
        if html_content.endswith("```"):
            html_content = html_content[:-3]  # Remove trailing ```
        
        html_content = html_content.strip()
        
        return html_content, cost_info
        
    except Exception as e:
        print(f"Error calling Claude API: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML files from build instructions using Claude API"
    )
    parser.add_argument(
        "build_instructions",
        help="Path to the build instructions file"
    )
    parser.add_argument(
        "output",
        help="Path for the output HTML file"
    )
    parser.add_argument(
        "--model", default=MODEL,
        help=f"Claude model (default {MODEL})"
    )
    parser.add_argument(
        "--effort", choices=["low", "medium", "high", "xhigh", "max"],
        help="Effort level (default: the model's own)"
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (optional, uses ANTHROPIC_API_KEY env var if not provided)"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: No API key provided. Set ANTHROPIC_API_KEY environment variable or use --api-key", file=sys.stderr)
        sys.exit(1)
    
    # Read build instructions
    print(f"Reading build instructions from: {args.build_instructions}", file=sys.stderr)
    instructions = read_file(args.build_instructions)
    
    # Generate HTML
    html_content, cost_info = generate_html(instructions, api_key, args.model, args.effort)
    
    # Display cost information
    print("\n" + "="*50, file=sys.stderr)
    print("API USAGE & COST", file=sys.stderr)
    print("="*50, file=sys.stderr)
    print(f"Input tokens:  {cost_info['input_tokens']:,}", file=sys.stderr)
    print(f"Output tokens: {cost_info['output_tokens']:,}", file=sys.stderr)
    print(f"Input cost:    ${cost_info['input_cost']:.4f}", file=sys.stderr)
    print(f"Output cost:   ${cost_info['output_cost']:.4f}", file=sys.stderr)
    print(f"Total cost:    ${cost_info['total_cost']:.4f}", file=sys.stderr)
    print("="*50 + "\n", file=sys.stderr)
    
    # Validate output looks like HTML
    if not html_content.strip().lower().startswith("<!doctype") and not html_content.strip().lower().startswith("<html"):
        print("Warning: Generated content may not be valid HTML", file=sys.stderr)
    
    # Write output
    write_file(args.output, html_content)
    print(f"HTML file generated successfully: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
