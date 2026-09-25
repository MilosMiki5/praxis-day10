#!/usr/bin/env python3
import base64
import json
import os
import sys


POINTS_PER_CRITERION = 1


def load_results(path):
    results = []
    with open(path, encoding="utf-8") as result_file:
        for line in result_file:
            line = line.rstrip("\n")
            if not line:
                continue
            status, _, description = line.partition("\t")
            description = description.strip()
            if description:
                results.append((status.strip().upper() == "PASS", description))
    return results


def build_result(results):
    tests = [
        {
            "name": description,
            "status": "pass" if passed else "fail",
            "score": POINTS_PER_CRITERION if passed else 0,
            "message": "" if passed else "Kriterium nicht erfüllt",
            "test_code": "",
            "filename": "",
            "line_no": 0,
            "duration": 0,
        }
        for passed, description in results
    ]

    return {
        "version": 1,
        "status": "pass" if all(test["status"] == "pass" for test in tests) else "fail",
        "max_score": len(tests) * POINTS_PER_CRITERION,
        "tests": tests,
    }


def emit(name, value):
    target = os.environ.get("GITHUB_OUTPUT")
    if not target:
        print(f"{name}={value}")
        return
    with open(target, "a", encoding="utf-8") as output_file:
        output_file.write(f"{name}={value}\n")


def main():
    path = os.environ.get("CLASSROOM_RESULTS")
    if not path or not os.path.isfile(path):
        print("report_score: keine Ergebnisdatei gefunden")
        return 0

    results = load_results(path)
    if not results:
        print("report_score: Ergebnisdatei ist leer")
        return 0

    result = build_result(results)
    score = sum(test["score"] for test in result["tests"])
    print(f"report_score: {score}/{result['max_score']} Punkte")

    encoded = base64.b64encode(json.dumps(result).encode("utf-8")).decode("ascii")
    emit("result", encoded)
    return 0


if __name__ == "__main__":
    sys.exit(main())
