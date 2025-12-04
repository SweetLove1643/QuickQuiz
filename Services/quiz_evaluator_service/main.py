from .tasks import evaluate_quiz


def main():
    """Main entry point for quiz evaluation.

    Reads JSON from stdin and outputs evaluation results to stdout.
    """
    import sys
    import json

    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Evaluate quiz
        result = evaluate_quiz(input_data)

        # Output JSON to stdout
        print(result)

    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON input: {e}"}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
