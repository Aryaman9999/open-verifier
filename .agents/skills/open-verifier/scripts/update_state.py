import json
import pathlib
import datetime
import sys
import argparse

# Path to the state file
STATE_PATH = pathlib.Path("out/state.json")

def update_state(step_name, status="complete", **kwargs):
    """
    Updates the verification pipeline state in state.json.
    Initializes the file if it doesn't exist.
    """
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text())
        except json.JSONDecodeError:
            data = {"schema_version": "1.0", "steps": {}}
    else:
        # Ensure the out/ directory exists
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {"schema_version": "1.0", "steps": {}}
    
    if "steps" not in data:
        data["steps"] = {}

    # Update the specific step
    # Use timezone-aware UTC (added in Python 3.11)
    timestamp = datetime.datetime.now(datetime.UTC).isoformat() + "Z"
    
    data["steps"][step_name] = {
        "status": status, 
        "timestamp": timestamp, 
        **kwargs
    }
    
    # Update the global 'last_updated' field
    data["last_updated"] = timestamp
    
    # Write back to disk
    STATE_PATH.write_text(json.dumps(data, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Open-Verifier state.json")
    parser.add_argument("step_name", help="Name of the step to update")
    parser.add_argument("--status", default="complete", help="Status of the step (default: complete)")
    parser.add_argument("--artifact", default=None, help="Path to the primary artifact produced by this step")
    parser.add_argument("--hash", default=None, help="SHA256 hash of the artifact")
    
    args = parser.parse_args()

    kwargs = {}
    if args.artifact:
        kwargs["artifact"] = args.artifact
    if args.hash:
        kwargs["hash"] = args.hash

    update_state(args.step_name, status=args.status, **kwargs)
